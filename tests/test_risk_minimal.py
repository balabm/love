import sys
sys.path.insert(0, ".")

from core.risk_manager import get_risk_manager
print("imported")
rm = get_risk_manager()
print("got instance")
rm.update_capital(11000)
print("updated capital")
status = rm.get_status()
print("got status", status)
sizing = rm.position_size(30000, 29000, "BTC")
print("got sizing", sizing)
print("OK")
