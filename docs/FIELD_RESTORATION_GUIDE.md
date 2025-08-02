# AI Inventory - Field Restoration Guide

## Overview
This guide helps restore missing custom fields after a site reinstall. The AI Inventory app requires several custom fields across different DocTypes for full functionality.

## Quick Restoration Commands

### 1. Basic Site Commands
```bash
cd /Users/sammishthundiyil/frappe-bench-ai

# Check site status
bench --site ai status

# Run migration
bench --site ai migrate

# Import fixtures (this should restore most fields)
bench --site ai import-fixtures

# Export updated fixtures after restoration
bench --site ai export-fixtures
```

### 2. Manual Field Creation (if needed)
If the fixtures don't restore all fields, use this Python script via bench:

```bash
bench --site ai execute "
import frappe

def create_field(dt, fieldname, label, fieldtype, insert_after, **kwargs):
    if frappe.db.exists('Custom Field', {'dt': dt, 'fieldname': fieldname}):
        print(f'✅ {dt}.{fieldname} exists')
        return
    
    field = frappe.get_doc({
        'doctype': 'Custom Field',
        'dt': dt,
        'fieldname': fieldname,
        'label': label,
        'fieldtype': fieldtype,
        'insert_after': insert_after,
        **kwargs
    })
    field.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f'✅ Created {dt}.{fieldname}')

# AI Inventory Forecast Fields
create_field('AI Inventory Forecast', 'auto_create_purchase_order', 'Auto Create Purchase Order', 'Check', 'reorder_alert', default='0')
create_field('AI Inventory Forecast', 'preferred_supplier', 'Preferred Supplier', 'Link', 'supplier', options='Supplier')

# Supplier Fields  
create_field('Supplier', 'supplier_segment', 'ML Supplier Segment', 'Select', 'supplier_group', options='\nStrategic\nPreferred\nApproved\nCaution\nCritical', read_only=1, in_list_view=1)
create_field('Supplier', 'deal_score', 'Deal Score', 'Int', 'supplier_segment', read_only=1, in_list_view=1)
create_field('Supplier', 'risk_score', 'Risk Score', 'Int', 'deal_score', read_only=1, in_list_view=1)
create_field('Supplier', 'last_ml_update', 'Last ML Update', 'Datetime', 'risk_score', read_only=1)

# Customer Fields
create_field('Customer', 'churn_probability', 'Churn Probability (%)', 'Float', 'customer_group', read_only=1, precision='2', in_list_view=1)
create_field('Customer', 'customer_lifetime_value', 'Customer Lifetime Value', 'Currency', 'churn_probability', read_only=1)
create_field('Customer', 'last_analytics_update', 'Last Analytics Update', 'Datetime', 'customer_lifetime_value', read_only=1)

# Item Fields
create_field('Item', 'forecasted_qty_30_days', 'Forecasted Qty (Next 30 Days)', 'Float', 'stock_uom', read_only=1, precision='2', in_list_view=1)
create_field('Item', 'demand_pattern', 'Demand Pattern', 'Select', 'forecasted_qty_30_days', options='\nStable\nIncreasing\nDecreasing\nSeasonal\nVolatile\nErratic', read_only=1)
create_field('Item', 'last_forecast_update', 'Last Forecast Update', 'Datetime', 'demand_pattern', read_only=1)

# Purchase Order Item Fields
create_field('Purchase Order Item', 'predicted_price', 'Predicted Price', 'Currency', 'rate', read_only=1)
create_field('Purchase Order Item', 'price_confidence', 'Price Confidence (%)', 'Int', 'predicted_price', read_only=1)

frappe.clear_cache()
print('🎉 Field creation completed!')
"
```

## Custom Fields Configuration

### AI Inventory Forecast DocType
| Field Name | Label | Type | Position | Description |
|------------|-------|------|----------|-------------|
| `auto_create_purchase_order` | Auto Create Purchase Order | Check | After `reorder_alert` | Auto-create PO when reorder alert triggers |
| `preferred_supplier` | Preferred Supplier | Link | After `supplier` | AI-recommended preferred supplier |

### Supplier DocType
| Field Name | Label | Type | Position | Description |
|------------|-------|------|----------|-------------|
| `supplier_segment` | ML Supplier Segment | Select | After `supplier_group` | ML-determined supplier classification |
| `deal_score` | Deal Score | Int | After `supplier_segment` | Deal quality score (0-100) |
| `risk_score` | Risk Score | Int | After `deal_score` | Risk score (0-100, lower is better) |
| `last_ml_update` | Last ML Update | Datetime | After `risk_score` | When ML analysis was last run |

### Customer DocType
| Field Name | Label | Type | Position | Description |
|------------|-------|------|----------|-------------|
| `churn_probability` | Churn Probability (%) | Float | After `customer_group` | AI-calculated probability of customer churn |
| `customer_lifetime_value` | Customer Lifetime Value | Currency | After `churn_probability` | AI-calculated customer lifetime value |
| `last_analytics_update` | Last Analytics Update | Datetime | After `customer_lifetime_value` | Last time AI analytics were updated |

### Item DocType
| Field Name | Label | Type | Position | Description |
|------------|-------|------|----------|-------------|
| `forecasted_qty_30_days` | Forecasted Qty (Next 30 Days) | Float | After `stock_uom` | AI-forecasted quantity for next 30 days |
| `demand_pattern` | Demand Pattern | Select | After `forecasted_qty_30_days` | AI-calculated demand pattern |
| `last_forecast_update` | Last Forecast Update | Datetime | After `demand_pattern` | Last time AI analytics were updated |

### Purchase Order Item DocType
| Field Name | Label | Type | Position | Description |
|------------|-------|------|----------|-------------|
| `predicted_price` | Predicted Price | Currency | After `rate` | AI-predicted price for this item |
| `price_confidence` | Price Confidence (%) | Int | After `predicted_price` | Confidence level of price prediction |

## Verification Commands

### Check Field Status
```bash
bench --site ai execute "
fields = frappe.get_all('Custom Field', 
    filters={'dt': ['in', ['AI Inventory Forecast', 'Supplier', 'Customer', 'Item', 'Purchase Order Item']]},
    fields=['dt', 'fieldname', 'label']
)

by_doctype = {}
for field in fields:
    dt = field['dt']
    if dt not in by_doctype:
        by_doctype[dt] = []
    by_doctype[dt].append(field)

print(f'📊 Total Custom Fields: {len(fields)}')
for dt, fields_list in by_doctype.items():
    print(f'{dt}: {len(fields_list)} fields')
    for field in fields_list:
        print(f'  • {field[\"fieldname\"]} - {field[\"label\"]}')
"
```

### Test AI Functionality
```bash
# Create test forecasts
bench --site ai execute "
from ai_inventory.ai_inventory.doctype.ai_inventory_forecast.ai_inventory_forecast import create_forecasts_for_all_existing_items
result = create_forecasts_for_all_existing_items()
print(f'Created {result.get(\"forecasts_created\", 0)} forecasts')
"

# Check ML dependencies
bench --site ai execute "
try:
    import numpy, pandas, sklearn
    print('✅ ML packages available')
except ImportError as e:
    print(f'❌ ML packages missing: {e}')
"
```

## File Locations

### Fixtures
- **Custom Fields**: `apps/ai_inventory/ai_inventory/fixtures/custom_field.json`
- **Property Setters**: `apps/ai_inventory/ai_inventory/fixtures/property_setter.json`

### Installation Scripts
- **Install Functions**: `apps/ai_inventory/ai_inventory/install.py`
- **Hooks Configuration**: `apps/ai_inventory/ai_inventory/hooks.py`

### Restoration Scripts
- **Field Restoration**: `apps/ai_inventory/restore_ai_fields.sh`
- **Manual Creation**: `apps/ai_inventory/create_fields.py`

## Troubleshooting

### Common Issues

1. **Fields not appearing in UI**
   ```bash
   bench --site ai clear-cache
   bench --site ai reload-doc ai_inventory "Custom Field" --force
   ```

2. **Permission errors**
   ```bash
   bench --site ai set-admin-password admin
   # Use administrator account for field creation
   ```

3. **Database schema issues**
   ```bash
   bench --site ai migrate
   bench --site ai repair
   ```

### Validation Queries

```sql
-- Check if custom fields exist
SELECT dt, fieldname, label, fieldtype 
FROM `tabCustom Field` 
WHERE dt IN ('AI Inventory Forecast', 'Supplier', 'Customer', 'Item', 'Purchase Order Item');

-- Count fields by doctype
SELECT dt, COUNT(*) as field_count 
FROM `tabCustom Field` 
WHERE dt IN ('AI Inventory Forecast', 'Supplier', 'Customer', 'Item', 'Purchase Order Item')
GROUP BY dt;
```

## Next Steps After Restoration

1. **Verify UI**: Check that all fields appear in forms
2. **Test Functionality**: Create test AI Inventory Forecasts
3. **Run Analytics**: Execute supplier analysis and customer analytics
4. **Setup Automation**: Configure scheduled tasks for AI updates
5. **Train Models**: Run initial ML model training if applicable

## Support

If you encounter issues:
1. Check the Error Log in ERPNext
2. Review bench logs: `bench --site ai logs`
3. Ensure all dependencies are installed
4. Verify database permissions

---

**Last Updated**: August 2, 2025
**AI Inventory Version**: Latest
**Compatible with**: Frappe v15+, ERPNext v15+
