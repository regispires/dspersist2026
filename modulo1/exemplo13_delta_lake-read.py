import pandas as pd
from deltalake import DeltaTable, write_deltalake, WriterProperties

path = "data/my_delta_rs"
dt = DeltaTable(path)
pat = dt.to_pyarrow_table()
print(pat)
print(pat.to_pandas())
