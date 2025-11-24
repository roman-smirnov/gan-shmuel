import pandas as pd

def parse_rates_file(filepath):
    # Read Excel file
    df = pd.read_excel(filepath)
    
    # Validate required columns exist
    required_columns = ['Product', 'Rate', 'Scope']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    rates = []
    
    for index, row in df.iterrows():
        # Validate each row has data
        product = row['Product']
        rate = row['Rate']
        scope = row['Scope']
        
        if pd.isna(product) or pd.isna(rate):
            raise ValueError(f"Row {index + 2} has missing Product or Rate")
        
        # Convert scope to string
        # 'All' stays as 'All', numbers become strings ('43' not 43)
        if pd.isna(scope):
            scope_str = 'All'
        elif isinstance(scope, (int, float)):
            scope_str = str(int(scope))
        else:
            scope_str = str(scope)
        
        rates.append({
            'product_id': str(product).strip(),
            'rate': int(rate),
            'scope': scope_str
        })
    
    return rates
