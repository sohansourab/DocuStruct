# Sample Receipts for DocuStruct Testing

This directory contains sample receipt and invoice images for testing and demonstration purposes.

## Current Samples

### Generic Receipts
- `receipt_cafe.png` - Coffee shop receipt with items and totals
- `receipt_grocery.png` - Supermarket receipt with multiple items
- `receipt_hardware.png` - Hardware store receipt with prices and tax

## Indian Receipts (Planned Q3 2026)

### Restaurants & Food
- `receipt_restaurant_delhi.png` - Delhi-based restaurant invoice
- `receipt_diner_bangalore.png` - Bangalore diner receipt
- `receipt_takeaway_mumbai.png` - Mumbai takeaway bill

### Retail & Commerce
- `receipt_pharmacy_delhi.png` - Medicine shop receipt (GST included)
- `receipt_retail_hyderabad.png` - Retail store bill with discounts
- `receipt_grocery_delhi.png` - Indian supermarket receipt

### Invoices
- `invoice_restaurant_goa.png` - Fine dining restaurant invoice
- `invoice_cafe_pune.png` - Café invoice with service charges

## International Samples (Planned Q4 2026)

### Europe
- `receipt_spain.png` - Spanish retail receipt
- `receipt_france.png` - French restaurant invoice
- `receipt_germany.png` - German store receipt

### Southeast Asia
- `receipt_thailand.png` - Thai restaurant bill
- `receipt_vietnam.png` - Vietnamese café receipt

## Using Samples

### CLI Testing
```bash
python3 app.py samples/*.png --report
```

### Streamlit Testing
1. Run `streamlit run streamlit_app.py`
2. Select samples from "Upload Document" section
3. View extraction results and analytics

## Evaluation Metrics

All sample receipts have **known expected outputs** for:
- Field accuracy testing
- Line-item extraction validation
- Tax calculation verification
- Date/time parsing

## Adding New Samples

When adding new receipt samples:

1. **Format:** PNG, JPG, or WEBP (max 2MB)
2. **Quality:** Well-lit, full-frame photo (no cropping)
3. **Content:** Real receipts with clear text
4. **Metadata:** Add to this README with region and type
5. **Groundtruth:** Create `<name>_expected.json` with correct extraction

Example groundtruth file (`receipt_cafe_expected.json`):
```json
{
  "store_name": "Café Downtown",
  "items": [
    {"description": "Cappuccino", "quantity": 1, "price": 4.50},
    {"description": "Croissant", "quantity": 2, "price": 3.50}
  ],
  "subtotal": 8.00,
  "tax": 0.64,
  "total": 8.64,
  "date": "2026-07-11",
  "time": "14:30"
}
```

## Sample Statistics

| Region | Count | Status | Languages |
|--------|-------|--------|-----------|
| Generic | 3 | Complete | English |
| India | 9 | Planned Q3 | English, Hindi |
| Europe | 3 | Planned Q4 | ES, FR, DE |
| Asia | 2 | Planned Q4 | Thai, Vietnamese |
| **Total** | **17** | **In Progress** | **7+** |
