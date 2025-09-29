import streamlit as st
st.title("Testing Basic Setup")
st.write("If you see this, Streamlit is working!")

# Try importing numpy
try:
    import numpy as np
    st.success(f"✅ NumPy {np.__version__} imported successfully")
except ImportError as e:
    st.error(f"❌ NumPy import failed: {e}")

# Try importing pandas
try:
    import pandas as pd
    st.success(f"✅ Pandas {pd.__version__} imported successfully")
except ImportError as e:
    st.error(f"❌ Pandas import failed: {e}")