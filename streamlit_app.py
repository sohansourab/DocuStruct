import sys
import hashlib
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0,str(Path(__file__).resolve().parent))

from evaluation import evaluate_runs
from pipeline import build_extractor, process_document
from storage import db


UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

APP_TITLE = "DocuStruct"
APP_TAGLINE = "Offline receipt and invoice intelligence for CPU-only, air-gapped workflows."
DEMO_USERNAME = "admin"
DEMO_PASSWORD = "docustruct"
LOGO_SVG = """
<svg width="92" height="92" viewBox="0 0 92 92" fill="none" xmlns="http://www.w3.org/2000/svg">
	<defs>
		<linearGradient id="g1" x1="14" y1="10" x2="78" y2="82" gradientUnits="userSpaceOnUse">
			<stop stop-color="#60A5FA"/>
			<stop offset="1" stop-color="#22D3EE"/>
		</linearGradient>
		<linearGradient id="g2" x1="18" y1="18" x2="72" y2="74" gradientUnits="userSpaceOnUse">
			<stop stop-color="#0F172A" stop-opacity="0.22"/>
			<stop offset="1" stop-color="#0F172A" stop-opacity="0.04"/>
		</linearGradient>
	</defs>
	<rect x="8" y="8" width="76" height="76" rx="22" fill="url(#g1)"/>
	<rect x="15" y="15" width="62" height="62" rx="18" fill="url(#g2)"/>
	<path d="M28 24H54L64 34V66C64 68.2091 62.2091 70 60 70H28C25.7909 70 24 68.2091 24 66V28C24 25.7909 25.7909 24 28 24Z" fill="white" fill-opacity="0.92"/>
	<path d="M54 24V34H64" stroke="#0F172A" stroke-opacity="0.18" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
	<path d="M31 39H57" stroke="#0F172A" stroke-opacity="0.6" stroke-width="4" stroke-linecap="round"/>
	<path d="M31 48H57" stroke="#0F172A" stroke-opacity="0.45" stroke-width="4" stroke-linecap="round"/>
	<path d="M31 57H48" stroke="#0F172A" stroke-opacity="0.3" stroke-width="4" stroke-linecap="round"/>
</svg>
"""

st.set_page_config(page_title="DocuStruct", page_icon="🧾", layout="wide")
db.init_db()


THEME_CSS = {
	"dark": """
	:root {
		--docu-bg: radial-gradient(circle at top, rgba(56, 189, 248, 0.16), transparent 30%), linear-gradient(180deg, #0b1020 0%, #090d18 100%);
		--docu-surface: rgba(17, 24, 39, 0.86);
		--docu-surface-2: rgba(30, 41, 59, 0.78);
		--docu-text: #eef2ff;
		--docu-muted: #a5b4fc;
		--docu-accent: #60a5fa;
		--docu-accent-2: #22d3ee;
		--docu-border: rgba(148, 163, 184, 0.18);
	}
	.stApp {
		background: var(--docu-bg);
		color: var(--docu-text);
	}
	[data-testid="stSidebar"] {
		background: linear-gradient(180deg, rgba(15, 23, 42, 0.98), rgba(11, 15, 29, 0.98));
		border-right: 1px solid var(--docu-border);
	}
	.main .block-container {
		padding-top: 2rem;
	}
	h1, h2, h3, h4, h5, h6, p, label, span, div {
		color: var(--docu-text);
	}
	[data-testid="stMetric"] {
		background: var(--docu-surface);
		border: 1px solid var(--docu-border);
		border-radius: 18px;
		padding: 0.9rem 1rem;
		box-shadow: 0 16px 40px rgba(0, 0, 0, 0.18);
	}
	[data-testid="stMetricLabel"] { color: var(--docu-muted); }
	[data-testid="stMetricValue"] { color: var(--docu-text); }
	.stButton > button, .stDownloadButton > button {
		background: linear-gradient(135deg, var(--docu-accent), var(--docu-accent-2));
		color: #06101f;
		border: 0;
		border-radius: 12px;
		font-weight: 700;
	}
	.stTabs [data-baseweb="tab-list"] {
		gap: 0.5rem;
	}
	.stTabs [data-baseweb="tab"] {
		background: var(--docu-surface-2);
		border-radius: 999px;
		padding: 0.55rem 1rem;
	}
	.stDataFrame, [data-testid="stDataFrame"] {
		border: 1px solid var(--docu-border);
		border-radius: 16px;
		overflow: hidden;
	}
	[data-testid="stExpander"] {
		border: 1px solid var(--docu-border);
		border-radius: 14px;
		background: rgba(15, 23, 42, 0.45);
	}
	""",
	"light": """
	:root {
		--docu-bg: linear-gradient(180deg, #f8fbff 0%, #eef4ff 100%);
		--docu-surface: rgba(255, 255, 255, 0.9);
		--docu-surface-2: rgba(241, 245, 249, 0.9);
		--docu-text: #10203a;
		--docu-muted: #5b6476;
		--docu-accent: #2563eb;
		--docu-accent-2: #14b8a6;
		--docu-border: rgba(15, 23, 42, 0.1);
	}
	.stApp {
		background: var(--docu-bg);
		color: var(--docu-text);
	}
	[data-testid="stSidebar"] {
		background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(241, 245, 249, 0.96));
		border-right: 1px solid var(--docu-border);
	}
	.main .block-container {
		padding-top: 2rem;
	}
	h1, h2, h3, h4, h5, h6, p, label, span, div {
		color: var(--docu-text);
	}
	[data-testid="stMetric"] {
		background: var(--docu-surface);
		border: 1px solid var(--docu-border);
		border-radius: 18px;
		padding: 0.9rem 1rem;
		box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
	}
	[data-testid="stMetricLabel"] { color: var(--docu-muted); }
	[data-testid="stMetricValue"] { color: var(--docu-text); }
	.stButton > button, .stDownloadButton > button {
		background: linear-gradient(135deg, var(--docu-accent), var(--docu-accent-2));
		color: white;
		border: 0;
		border-radius: 12px;
		font-weight: 700;
	}
	.stTabs [data-baseweb="tab-list"] {
		gap: 0.5rem;
	}
	.stTabs [data-baseweb="tab"] {
		background: var(--docu-surface-2);
		border-radius: 999px;
		padding: 0.55rem 1rem;
	}
	.stDataFrame, [data-testid="stDataFrame"] {
		border: 1px solid var(--docu-border);
		border-radius: 16px;
		overflow: hidden;
	}
	[data-testid="stExpander"] {
		border: 1px solid var(--docu-border);
		border-radius: 14px;
		background: rgba(255, 255, 255, 0.75);
	}
	""",
}


def apply_theme(theme: str) -> None:
	st.markdown(f"<style>{THEME_CSS[theme]}</style>", unsafe_allow_html=True)


def render_brand_header() -> None:
	st.markdown(
		f"""
		<div style="display:flex;align-items:center;gap:1rem;margin:0.5rem 0 1.25rem 0;">
		  <div style="width:92px;min-width:92px;">{LOGO_SVG}</div>
		  <div>
		    <div style="font-size:3rem;font-weight:900;line-height:1;color:var(--docu-text);letter-spacing:-0.04em;">{APP_TITLE}</div>
		    <div style="margin-top:0.4rem;font-size:1rem;max-width:760px;color:var(--docu-muted);">{APP_TAGLINE}</div>
		  </div>
		</div>
		""",
		unsafe_allow_html=True,
	)


def render_login_page() -> None:
	render_brand_header()
	st.markdown(
		"""
		<div style="max-width:760px;margin:1rem 0 2rem 0;padding:1.5rem 1.75rem;border-radius:24px;
		background:var(--docu-surface);border:1px solid var(--docu-border);box-shadow:0 24px 60px rgba(15,23,42,0.16);">
		  <div style="color:var(--docu-text);font-size:1rem;line-height:1.7;">
		    Sign in to review OCR results, stored documents, and analytics. This local login is a demo gate for the hackathon prototype.
		  </div>
		</div>
		""",
		unsafe_allow_html=True,
	)
	with st.form("login_form", clear_on_submit=False):
		username = st.text_input("Username", placeholder="admin")
		password = st.text_input("Password", type="password", placeholder="docustruct")
		submitted = st.form_submit_button("Sign in")
		if submitted:
			if username == DEMO_USERNAME and password == DEMO_PASSWORD:
				st.session_state.authenticated = True
				st.session_state.username = username
				st.rerun()
			st.error("Invalid credentials. Use the demo login provided in the project notes.")

if "extractor" not in st.session_state:
	st.session_state.extractor = build_extractor("rule_based")
if "processed_hashes" not in st.session_state:
	st.session_state.processed_hashes = set()
if "recent_results" not in st.session_state:
	st.session_state.recent_results = []

if "theme_mode" not in st.session_state:
	st.session_state.theme_mode = "dark"

if "authenticated" not in st.session_state:
	st.session_state.authenticated = False

if "username" not in st.session_state:
	st.session_state.username = ""

with st.sidebar:
	theme_choice = st.radio("Theme", ["dark", "light"], index=0 if st.session_state.theme_mode == "dark" else 1, horizontal=True)
	if theme_choice != st.session_state.theme_mode:
		st.session_state.theme_mode = theme_choice

apply_theme(st.session_state.theme_mode)

if not st.session_state.authenticated:
	render_login_page()
	st.stop()

with st.sidebar:
	st.caption(f"Signed in as `{st.session_state.username}`")
	if st.button("Logout"):
		st.session_state.authenticated = False
		st.session_state.username = ""
		st.rerun()


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

render_brand_header()


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