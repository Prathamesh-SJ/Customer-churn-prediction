import pickle
import pandas as pd
import streamlit as st

@st.cache_resource
def load_assets():
    with open("xgb_churn_model.pkl", "rb") as f:
        model = pickle.load(f)
    with open("scaler.pkl", "rb") as f:
        scaler = pickle.load(f)
    return model, scaler

model, scaler = load_assets()

st.title("Customer Churn Predictor")
st.write("Answer these simple questions to check if a customer is likely to leave or stay.")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Plan Details")
    tenure = st.slider("How many months have they been a customer?", 1, 72, 24)
    contract = st.selectbox("What is their current plan type?", 
                            options=['month_to_month', 'one_year', 'two_year'],
                            format_func=lambda x: x.replace('_', ' ').title())
    monthlycharges = st.number_input("What is their current monthly bill? (₹)", min_value=100.0, value=699.0, step=50.0)
    num_services = st.slider("How many total services or add-ons do they use?", 1, 6, 2)
    gender = st.selectbox("Gender", ['Male', 'Female', 'Other'])

with col2:
    st.markdown("### Customer History")
    annual_income = st.number_input("What is their annual income? (₹)", min_value=10000.0, value=600000.0, step=25000.0)
    customer_satisfaction = st.slider("How happy are they with the service? (1 = Unhappy, 9 = Very Happy)", 1.0, 9.0, 7.0)
    num_complaints = st.number_input("How many complaints have they filed?", min_value=0, max_value=10, value=0)
    num_service_calls = st.number_input("How many times have they called support?", min_value=0, max_value=15, value=1)
    late_payments = st.number_input("How many times did they miss a payment this year?", min_value=0, max_value=12, value=0)
    days_since_last_interaction = st.number_input("How many days ago was their last activity?", min_value=0, max_value=365, value=14)

if st.button("Predict Churn Risk", type="primary", use_container_width=True):
    
    full_input = {
        'tenure': tenure, 
        'monthlycharges': monthlycharges, 
        'customer_satisfaction': customer_satisfaction, 
        'num_complaints': num_complaints,
        'num_services': num_services,
        'num_service_calls': num_service_calls,
        'late_payments': late_payments,
        'days_since_last_interaction': days_since_last_interaction,
        'annual_income': annual_income,
        'age': 40,
        'dependents': 0, 
        'senior_citizen': 0, 
        'totalcharges': tenure * monthlycharges, 
        'has_phone_service': 1, 
        'has_internet_service': 1, 
        'has_online_security': 0, 
        'has_online_backup': 0, 
        'has_device_protection': 0, 
        'has_tech_support': 0, 
        'has_streaming_tv': 0, 
        'has_streaming_movies': 0, 
        'avg_monthly_gb': 45.0, 
        'credit_score': 720.0, 
        'paperless_billing': 1
    }
    
    df_raw = pd.DataFrame([full_input])
    
    df_raw['charges_per_service'] = df_raw['monthlycharges'] / (df_raw['num_services'] + 1)
    df_raw['complaints_per_call'] = df_raw['num_complaints'] / (df_raw['num_service_calls'] + 1)
    df_raw['income_per_dependent'] = df_raw['annual_income'] / (df_raw['dependents'] + 1)
    df_raw['satisfaction_complaint_ratio'] = df_raw['customer_satisfaction'] / (df_raw['num_complaints'] + 1)
    df_raw['tenure_charge_ratio'] = df_raw['tenure'] / (df_raw['monthlycharges'] + 1)
    
    all_features = model.get_booster().feature_names
    for col in all_features:
        if '_' in col and col not in df_raw.columns:
            df_raw[col] = False
            
    if f"contract_{contract}" in df_raw.columns:
        df_raw[f"contract_{contract}"] = True
        
    if f"gender_{gender}" in df_raw.columns:
        df_raw[f"gender_{gender}"] = True
        
    if "education_bachelor" in df_raw.columns: df_raw["education_bachelor"] = True
    if "marital_status_single" in df_raw.columns: df_raw["marital_status_single"] = True
    if "payment_method_credit_card" in df_raw.columns: df_raw["payment_method_credit_card"] = True

    num_cols = list(scaler.feature_names_in_)
    df_raw[num_cols] = scaler.transform(df_raw[num_cols].astype(float))
    
    df_processed = df_raw[all_features]
    prob = float(model.predict_proba(df_processed)[:, 1][0])
    
    st.divider()
    if prob >= 0.50:
        st.error(f"High Risk of Churn (Probability: {prob:.1%})")
    else:
        st.success(f"Low Risk of Churn (Probability: {prob:.1%})")