# THE MATRIX - Windows Setup Guide

## 🪟 Step-by-Step Windows Installation

### Step 1: Download the Matrix Scanner

**Option A: From Claude (easiest)**
1. Look for the folder icon in my previous message
2. Click to download `matrix_scanner` folder
3. Save it to your Desktop or Documents

**Option B: Manual extraction**
1. Extract all files from the download
2. Place them in: `C:\Users\Michael Dingamadji\matrix_scanner`

### Step 2: Fix PATH Issue (Important!)

Your Python Scripts folder is not in PATH. Here's how to add it:

**Method 1: Quick Command (Run in PowerShell as Administrator)**
```powershell
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
$NewPath = $UserPath + ";C:\Users\Michael Dingamadji\AppData\Roaming\Python\Python314\Scripts"
[Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
```

**Method 2: Manual (if command doesn't work)**
1. Press `Windows Key + R`
2. Type: `sysdm.cpl` and press Enter
3. Click "Advanced" tab → "Environment Variables"
4. Under "User variables", select "Path" → Click "Edit"
5. Click "New"
6. Add: `C:\Users\Michael Dingamadji\AppData\Roaming\Python\Python314\Scripts`
7. Click OK on all windows
8. **CLOSE and REOPEN PowerShell**

### Step 3: Navigate to Matrix Scanner

Open PowerShell and run:
```powershell
cd "C:\Users\Michael Dingamadji\matrix_scanner"
```

Or if you put it on Desktop:
```powershell
cd "C:\Users\Michael Dingamadji\Desktop\matrix_scanner"
```

Or if you put it in Documents:
```powershell
cd "C:\Users\Michael Dingamadji\Documents\matrix_scanner"
```

### Step 4: Run Setup (One-Time)

**Option A: Use the batch file**
```powershell
.\SETUP_WINDOWS.bat
```

**Option B: Manual install**
```powershell
python -m pip install --user streamlit yfinance pandas numpy plotly pandas-datareader
```

### Step 5: Start the Scanner

**Option A: Use the batch file**
```powershell
.\RUN_WINDOWS.bat
```

**Option B: Manual run**
```powershell
python -m streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

---

## 🔧 Troubleshooting

### Error: "streamlit is not recognized"

**Cause**: Python Scripts not in PATH

**Fix**: 
```powershell
# Use python -m instead
python -m streamlit run app.py
```

### Error: "Cannot find path matrix_scanner"

**Cause**: You're in the wrong directory

**Fix**:
```powershell
# Find where you downloaded it
cd Desktop\matrix_scanner
# OR
cd Documents\matrix_scanner
# OR
cd Downloads\matrix_scanner
```

### Error: Module not found

**Cause**: Dependencies not installed

**Fix**:
```powershell
python -m pip install --user streamlit yfinance pandas numpy plotly
```

### Port already in use

**Cause**: Streamlit already running

**Fix**:
```powershell
# Kill the process
taskkill /F /IM streamlit.exe

# Or use a different port
python -m streamlit run app.py --server.port 8502
```

---

## ✅ Quick Verification

After setup, verify everything works:

```powershell
# Check Python
python --version
# Should show: Python 3.14.x

# Check Streamlit
python -m streamlit --version
# Should show: Streamlit, version 1.52.x

# Check location
pwd
# Should show: ...\matrix_scanner

# List files
dir
# Should see: app.py, README.md, etc.
```

---

## 🚀 Daily Usage (After Setup)

1. Open PowerShell
2. Navigate to matrix_scanner:
   ```powershell
   cd "C:\Users\Michael Dingamadji\matrix_scanner"
   ```
3. Run:
   ```powershell
   .\RUN_WINDOWS.bat
   ```
4. Browser opens automatically
5. Enter ticker and scan!

---

## 🎯 What to Do RIGHT NOW

### Immediate Steps:

1. **Download the matrix_scanner folder** (from my message above)
   
2. **Place it here**: `C:\Users\Michael Dingamadji\matrix_scanner`

3. **Open PowerShell** (not as admin)

4. **Run these commands ONE AT A TIME**:
   ```powershell
   cd "C:\Users\Michael Dingamadji\matrix_scanner"
   
   python -m pip install --user streamlit yfinance pandas numpy plotly
   
   python -m streamlit run app.py
   ```

5. **Browser should open** - you're done! 🎉

---

## 📁 Expected Folder Structure

After downloading, you should have:

```
C:\Users\Michael Dingamadji\matrix_scanner\
├── app.py
├── market_memory.py
├── regime_detection.py
├── numerology.py
├── ma_system.py
├── technical_analysis.py
├── strategy_backtester.py
├── requirements.txt
├── README.md
├── QUICKSTART.md
├── IMPLEMENTATION_GUIDE.md
├── SETUP_WINDOWS.bat
└── RUN_WINDOWS.bat
```

---

## 💡 Pro Tips for Windows

### Create Desktop Shortcut:

1. Right-click on Desktop → New → Shortcut
2. Location: 
   ```
   C:\Windows\System32\cmd.exe /c "cd /d C:\Users\Michael Dingamadji\matrix_scanner && python -m streamlit run app.py"
   ```
3. Name it: "Matrix Scanner"
4. Change icon if you want
5. **Double-click to launch!**

### Pin to Taskbar:

1. Create the shortcut above
2. Right-click it → Pin to Taskbar
3. Now it's always one click away

### Auto-open browser:

The batch file already does this, but if running manually:
```powershell
python -m streamlit run app.py --server.headless false
```

---

## 🔄 Updating Later

When you want to update the code:

```powershell
cd matrix_scanner
python -m pip install --upgrade streamlit yfinance pandas
```

---

## ⚠️ Common Mistakes to Avoid

1. ❌ Don't copy error messages as commands
2. ❌ Don't run multiple streamlit instances
3. ❌ Don't forget to `cd` into the folder first
4. ❌ Don't use `streamlit run` if PATH not fixed
5. ✅ DO use `python -m streamlit run` instead

---

## 🆘 Still Having Issues?

### Quick Diagnostic:

Run this in PowerShell:
```powershell
# Show Python location
where.exe python

# Show Python version
python --version

# Show current directory
pwd

# Show installed packages
python -m pip list | Select-String streamlit
```

Send me the output and I'll help debug!

---

## 🎓 Next Steps After Setup

Once it's running:

1. **Read QUICKSTART.md** - 5-minute tutorial
2. **Try scanning SPY** - Your first test
3. **Review README.md** - Full documentation
4. **Study the Sequence** - Learn the 10 floors

---

Remember: Use `python -m streamlit run app.py` instead of just `streamlit run app.py` until you fix your PATH!
