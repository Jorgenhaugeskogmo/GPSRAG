"""
NumPy 2.0 Compatibility Layer for ChromaDB
MUST be imported before any ChromaDB imports
"""

import sys
import numpy as np

# Force NumPy 1.x compatibility for ChromaDB
def patch_numpy_compatibility():
    """Force NumPy 1.x behavior for ChromaDB compatibility"""
    
    # Add missing deprecated attributes that ChromaDB expects
    if not hasattr(np, 'float_'):
        np.float_ = np.float64
        print("✅ Patched np.float_ -> np.float64")
    
    if not hasattr(np, 'int_'):
        np.int_ = np.int64
        print("✅ Patched np.int_ -> np.int64")
    
    if not hasattr(np, 'bool_'):
        np.bool_ = np.bool8
        print("✅ Patched np.bool_ -> np.bool8")
    
    if not hasattr(np, 'complex_'):
        np.complex_ = np.complex128
        print("✅ Patched np.complex_ -> np.complex128")
    
    # Additional patches for specific ChromaDB issues
    if not hasattr(np, 'unicode_'):
        np.unicode_ = np.str_
        print("✅ Patched np.unicode_ -> np.str_")
    
    if not hasattr(np, 'str_'):
        np.str_ = str
        print("✅ Patched np.str_ -> str")
    
    print(f"🔧 NumPy {np.__version__} compatibility patches applied for ChromaDB")
    return True

# Apply patches immediately when module is imported
patch_numpy_compatibility() 