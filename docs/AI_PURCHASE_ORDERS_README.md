# 🤖 AI-Powered Purchase Order System

## Overview

The AI-Powered Purchase Order system uses Machine Learning algorithms and sales forecasting data to automatically create optimized Purchase Orders. This system analyzes sales patterns, inventory levels, and supplier performance to generate intelligent procurement recommendations.

## Features

### 🎯 Core AI Capabilities

1. **ML-Driven Quantity Optimization**
   - Analyzes historical sales data and current forecasts
   - Calculates optimal order quantities using AI algorithms
   - Considers lead times, safety stock, and demand patterns

2. **Smart Supplier Selection**
   - AI-powered supplier scoring and analysis
   - Groups items by optimal suppliers
   - Considers price competitiveness and delivery performance

3. **Urgency Detection**
   - Real-time stock level analysis
   - AI-determined purchase priorities (🚨 URGENT, 🔴 HIGH, 🟡 MEDIUM, 🟢 LOW)
   - Critical item identification based on movement patterns

4. **Confidence Scoring**
   - AI confidence levels for each recommendation
   - Predictive accuracy tracking
   - Risk assessment for purchase decisions

### 📊 AI Analytics Integration

The system integrates with the AI Sales Forecast module to:
- Use sales predictions for demand planning
- Leverage movement type classifications (Critical, Fast Moving, Slow Moving)
- Apply confidence scores to purchase recommendations
- Consider seasonal patterns and trends

### 🛠️ Usage

#### Access from AI Sales Dashboard

1. **Navigate to AI Sales Dashboard**
   ```
   Desk → AI Inventory → AI Sales Dashboard
   ```

2. **AI Purchase Order Buttons**
   - **📦 Bulk Purchase Orders**: Create AI-optimized Purchase Orders
   - **📊 Purchase Insights**: View AI analytics without creating POs
   - **🎯 Smart Procurement**: Advanced procurement planning (future feature)

#### Creating AI Purchase Orders

1. **Click "📦 Bulk Purchase Orders"**
2. **Configure AI Parameters:**
   - Company: Select your company
   - Territory: Optional territory filter
   - Minimum AI Confidence %: Filter by prediction confidence (default: 70%)
   - Minimum Predicted Quantity: Exclude low-demand items (default: 1)

3. **AI Analysis Options:**
   - ✅ Prioritize Critical Items: Focus on critical stock situations
   - ✅ Include AI Safety Stock: Add intelligent safety stock calculations
   - ✅ Group by Supplier: Create separate POs for each supplier
   - ☐ Auto Submit POs: Automatically submit high-confidence POs

4. **Click "🚀 Create AI Purchase Orders"**

#### Viewing Purchase Insights

1. **Click "📊 Purchase Insights"**
2. **Set Analysis Parameters:**
   - Company and Territory filters
   - Minimum confidence threshold

3. **Review AI Analysis:**
   - Items analyzed and confidence levels
   - Critical items requiring immediate attention
   - Supplier analysis and recommendations
   - Top purchase opportunities

### 🏗️ Technical Architecture

#### AI Purchase Order Fields

**Purchase Order (Header):**
- `ai_generated`: Checkbox indicating AI creation
- `ai_confidence_score`: Overall confidence percentage
- `ai_purchase_priority`: AI-determined priority level
- `ai_insights`: Detailed AI recommendations and analysis

**Purchase Order Item:**
- `ai_optimized_qty`: AI-calculated optimal quantity
- `ai_movement_type`: Item movement classification
- `ai_purchase_urgency`: Urgency level assessment
- `ai_confidence_score`: Item-specific confidence score
- `predicted_price`: ML-predicted optimal price
- `price_confidence`: Price prediction confidence

#### AI Algorithms

1. **Quantity Optimization:**
   ```python
   # Simplified algorithm
   lead_time_demand = (predicted_qty / 30) * lead_time_days
   ai_safety_stock = max(safety_stock, lead_time_demand * 0.5) * movement_multiplier
   optimized_qty = (predicted_qty + lead_time_demand + ai_safety_stock) * confidence_factor
   ```

2. **Urgency Assessment:**
   - 🚨 URGENT: Out of stock or critical items
   - 🔴 HIGH: Below 50% of reorder level
   - 🟡 MEDIUM: Near reorder level
   - 🟢 LOW: Adequate stock levels

3. **Supplier Scoring:**
   - Price competitiveness analysis
   - Lead time performance
   - Historical reliability metrics

### 📈 Benefits

1. **Reduced Stockouts**: AI predicts demand patterns to prevent stock shortages
2. **Optimized Inventory**: Calculates precise order quantities to minimize excess stock
3. **Cost Savings**: Intelligent supplier selection and quantity optimization
4. **Time Efficiency**: Automated PO creation reduces manual procurement work
5. **Risk Mitigation**: Confidence scoring helps assess purchase decision risks
6. **Data-Driven Decisions**: ML algorithms provide objective procurement recommendations

### 🔧 Configuration

#### Prerequisites

1. **AI Sales Forecast Data**: Ensure AI sales forecasting is active and populated
2. **Supplier Master**: Configure default suppliers for items
3. **Item Master**: Set up proper item codes, UOMs, and lead times
4. **Warehouse Configuration**: Default warehouses for companies

#### Custom Field Installation

The system automatically installs custom fields during app installation:

- Purchase Order AI fields
- Purchase Order Item AI fields
- Enhanced analytics tracking

### 🧪 Testing

Use the test script to verify functionality:

```bash
cd /path/to/frappe-bench
bench execute ai_inventory.test_ai_purchase_orders.main
```

### 📚 API Reference

#### Main Functions

```python
# Create bulk AI Purchase Orders
create_bulk_purchase_orders_from_ai_analytics(filters)

# Get AI purchase insights
get_purchase_order_ai_insights(filters)

# Calculate AI-optimized quantities
calculate_ai_optimized_purchase_qty(forecast_row)

# Determine purchase urgency
determine_purchase_urgency(forecast_row)
```

### 🎯 Future Enhancements

1. **Advanced ML Models**: Integration with scikit-learn for more sophisticated predictions
2. **Supplier Performance ML**: AI-driven supplier rating and selection
3. **Price Prediction**: ML-based price forecasting and optimization
4. **Automated Approval**: Smart approval workflows based on confidence scores
5. **Integration with Procurement Apps**: Connect with third-party procurement platforms

### 🆘 Troubleshooting

#### Common Issues

1. **No AI Forecast Data**: Run sales forecast sync from AI Sales Dashboard
2. **Missing Suppliers**: Ensure items have default suppliers configured
3. **Zero Quantities**: Check minimum confidence and quantity thresholds
4. **Custom Fields Missing**: Run `bench migrate` to install custom fields

#### Support

For issues or feature requests:
- Create GitHub issues in the ai_inventory repository
- Contact: sammish.thundiyil@gmail.com

---

**🚀 Powered by AI & Machine Learning for Smarter Procurement**
