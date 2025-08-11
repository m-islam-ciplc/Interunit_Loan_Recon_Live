# Server Controls - Start & Stop

## 🚀 Start Production Server

```bash
cd /opt/Interunit_Loan_Recon_Live
source .venv/bin/activate
gunicorn app_interunit_loan_recon:app --bind 0.0.0.0:5001 --workers 4 --daemon
```

## 🛑 Stop Production Server

```bash
pkill -f "app_interunit_loan_recon:app"
```

## ✅ Check if Server is Running

```bash
ps aux | grep gunicorn
```

## 🔄 Restart Server

```bash
# Stop first
pkill -f "app_interunit_loan_recon:app"

# Wait 2 seconds
sleep 2

# Start again
cd /opt/Interunit_Loan_Recon_Live
source .venv/bin/activate
gunicorn app_interunit_loan_recon:app --bind 0.0.0.0:5001 --workers 4 --daemon
```

## 📍 Quick Reference

| Action | Command |
|--------|---------|
| **Start** | `gunicorn app_interunit_loan_recon:app --bind 0.0.0.0:5001 --workers 4 --daemon` |
| **Stop** | `pkill -f "app_interunit_loan_recon:app"` |
| **Check** | `ps aux | grep gunicorn` |

## 💡 Notes

- Server runs on port **5001**
- Uses **4 workers** for better performance
- **--daemon** flag keeps it running in background
- Server survives SSH disconnections
- Always run from `/opt/Interunit_Loan_Recon_Live` directory
