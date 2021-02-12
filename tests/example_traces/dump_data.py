import numpy as np

for f in ["calcium_data.npy", "voltage_data.npy"]:
    d = np.load("calcium_data.npy", allow_pickle=True).item()
    d.pop("chopping_parameters", None)
    np.save(f, d)
