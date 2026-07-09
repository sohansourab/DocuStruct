import sys
import hashlib
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent))

from evaluation import evaluate_runs
from pipeline import build_extractor, process_document
from storage import db


UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="DocuStruct", page_icon="🧾", layout="wide")
db.init_db()

if "extractor" not in st.session_state:
	st.session_state.extractor = build_extractor("rule_based")
if "processed_hashes" not in st.session_state:
	st.session_state.processed_hashes = set()
if "recent_results" not in st.session_state:
	st.session_state.recent_results = []


def run_pipeline(path: str, source_label: str | None = None) -> dict:
	return process_document(path, st.session_state.extractor, source_label=source_label)


def save_upload(file_bytes: bytes, suggested_name: str) -> str:
	h = hashlib.sha256(file_bytes).hexdigest()[:16]
	ext = Path(suggested_name).suffix or ".png"
	out_path = UPLOAD_DIR / f"{h}{ext}"
	if not out_path.exists():
		out_path.write_bytes(file_bytes)
	return str(out_path)


def confidence_badge(score: float) -> str:
	if score >= 0.75:
		return f":green[**{score:.2f}** ✅]"
	if score >= 0.5:
		return f":orange[**{score:.2f}** ⚠️]"
	return f":red[**{score:.2f}** ❌]"


st.sidebar.title("🧾 DocuStruct")
st.sidebar.caption("Offline receipt/invoice → structured data")
page = st.sidebar.radio("Go to", ["📤 Upload & Process", "🗄️ Database Explorer", "📊 Analytics"])
st.sidebar.divider()
st.sidebar.caption(f"DB: `{db.DB_PATH.name}`")
st.sidebar.caption("100% local · Tesseract OCR · SQLite · no network calls")


if page == "📤 Upload & Process":
	st.title("Upload & Process")
	st.write(
		"Drop in receipt images (or use your camera) and each one is OCR'd, "
		"extracted, validated, and stored the moment it lands — no batch step."
	)

	tab_upload, tab_camera = st.tabs(["📁 File upload", "📷 Camera capture"])
	new_files = []

	with tab_upload:
		uploaded = st.file_uploader(
			"Receipt / invoice images",
			type=["png", "jpg", "jpeg", "webp"],
			accept_multiple_files=True,
		)
		if uploaded:
			new_files.extend(uploaded)

	with tab_camera:
		st.caption("Snap a photo of a receipt directly — processed immediately on capture.")
		cam_shot = st.camera_input("Capture receipt")
		if cam_shot is not None:
			new_files.append(cam_shot)

	for f in new_files:
		file_bytes = f.getvalue()
		content_hash = hashlib.sha256(file_bytes).hexdigest()
		source_label = getattr(f, "name", "capture.png")
		path = save_upload(file_bytes, source_label)

		with st.container(border=True):
			cols = st.columns([1, 2])
			cols[0].image(file_bytes, caption=Path(path).name, use_container_width=True)

			already_seen = content_hash in st.session_state.processed_hashes
			with cols[1]:
				with st.spinner("Running OCR → extraction → validation..."):
					result = run_pipeline(path, source_label=source_label)
				st.session_state.processed_hashes.add(content_hash)
				st.session_state.recent_results.append(result)

				if result["error"]:
					st.error(result["error"])
					continue

				doc = result["structured"]
				metrics = st.columns(4)
				metrics[0].metric("Vendor", doc.vendor or "—")
				metrics[1].metric("Total", f"{doc.total:.2f}" if doc.total is not None else "—")
				metrics[2].metric("Wall time", f"{result['total_wall_ms']} ms")
				metrics[3].markdown(f"**Confidence**  \n{confidence_badge(result['structured'].overall_confidence)}")

				cache_note = " (from OCR cache)" if result["ocr_from_cache"] else ""
				st.caption(f"OCR status: **{result['ocr_status']}**{cache_note} · stored as document #{result['doc_id']}")

				if result["validation_issues"]:
					st.warning("Validation issues: " + ", ".join(result["validation_issues"]))
				else:
					st.success("Validation: clean (arithmetic cross-checks passed)")

				if already_seen:
					st.info("This exact image was already processed this session — re-shown from OCR cache.")

				st.caption("Full structured output, raw OCR text, and line items are available in Database Explorer.")


elif page == "🗄️ Database Explorer":
	st.title("Database Explorer")
	rows = db.query_documents(min_confidence=0.0)
	if not rows:
		st.info("No documents stored yet — head to Upload & Process to add some.")
	else:
		df = pd.DataFrame(rows)
		c1, c2, c3 = st.columns([2, 2, 2])
		min_conf = c1.slider("Min. confidence", 0.0, 1.0, 0.0, 0.05)
		vendor_filter = c2.text_input("Filter by vendor (contains)")
		only_issues = c3.checkbox("Only show rows with validation issues")

		view = df[df["overall_confidence"] >= min_conf]
		if vendor_filter:
			view = view[view["vendor"].str.contains(vendor_filter, case=False, na=False)]
		if only_issues:
			view = view[view["validation_issues_json"].apply(lambda s: s not in ("[]", "", None))]

		st.dataframe(
			view[["id", "vendor", "document_date", "total", "overall_confidence", "extractor_used", "processing_ms", "created_at"]],
			use_container_width=True,
			hide_index=True,
		)

		st.subheader("Line items for a document")
		if not view.empty:
			doc_id = st.selectbox("Document ID", view["id"].tolist())
			items = db.get_line_items(int(doc_id))
			if items:
				st.table(pd.DataFrame(items)[["description", "quantity", "unit_price", "line_total"]])
			else:
				st.caption("No line items recorded for this document.")


elif page == "📊 Analytics":
	st.title("Analytics")
	rows = db.query_documents(min_confidence=0.0)
	if not rows:
		st.info("No documents stored yet — head to Upload & Process to add some.")
	else:
		df = pd.DataFrame(rows)
		k1, k2, k3, k4 = st.columns(4)
		k1.metric("Documents processed", len(df))
		k2.metric("Avg confidence", f"{df['overall_confidence'].mean():.2f}")
		k3.metric("Avg processing time", f"{df['processing_ms'].mean():.1f} ms")
		k4.metric("Total value captured", f"${df['total'].sum():,.2f}")

		c1, c2 = st.columns(2)
		with c1:
			st.plotly_chart(px.histogram(df, x="overall_confidence", nbins=10, title="Confidence distribution"), use_container_width=True)
		with c2:
			spend = df.groupby("vendor", dropna=True)["total"].sum().reset_index()
			st.plotly_chart(px.bar(spend, x="vendor", y="total", title="Total spend by vendor"), use_container_width=True)

		st.subheader("Hackathon Scorecard")
		if st.session_state.recent_results:
			scorecard = evaluate_runs(st.session_state.recent_results)
			score_cols = st.columns(4)
			score_cols[0].metric("Overall score", f"{scorecard['overall_score']}/100")
			score_cols[1].metric("Field accuracy", f"{scorecard['field_accuracy']:.3f}" if scorecard["field_accuracy"] is not None else "n/a")
			score_cols[2].metric("Validation pass rate", f"{scorecard['validation_pass_rate']:.3f}")
			score_cols[3].metric("Offline success", f"{scorecard['offline_success_rate']:.3f}")
			st.caption(f"Ground-truth cases scored: {scorecard['known_cases']}" if scorecard["known_cases"] else "Upload one of the bundled sample receipts to compute ground-truth field accuracy.")
		else:
			st.caption("Process a receipt in this session to populate the scorecard.")

		st.subheader("Documents over time")
		timeline = df.copy()
		timeline["created_at"] = pd.to_datetime(timeline["created_at"], errors="coerce")
		timeline["total"] = pd.to_numeric(timeline["total"], errors="coerce")
		timeline = timeline.dropna(subset=["created_at", "overall_confidence", "total"])
		if timeline.empty:
			st.caption("Not enough complete documents yet to draw the timeline scatter.")
		else:
			st.plotly_chart(
				px.scatter(
					timeline.sort_values("created_at"),
					x="created_at",
					y="overall_confidence",
					color="vendor",
					size="total",
					title="Confidence & value over time",
				),
				use_container_width=True,
			)