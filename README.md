# I Told U

A lightweight push-to-talk app that turns speech into text for any active window. Hold the hotkey, speak, release, and the app recognizes your speech, optionally translates it through DeepSeek, and pastes the result where your cursor was focused: Telegram, VS Code, a browser, a document, and more.

![I Told U screenshot](docs/assets/screenshot.png)

## What It Does

- Push-to-talk: records only while you hold the configured key.
- Pastes into the active window after you release the hotkey.
- Speech-to-text only mode: speech goes straight to text.
- Translation mode: recognized text is sent through DeepSeek into your chosen target language.
- Physical hotkey capture: left and right keys with the same label can be distinguished.
- Small status overlay in the corner: recording, processing, and pasting.
- Windows autostart and start-minimized support.
- API key can come from `.env` or be saved from inside the app. Local Windows storage is encrypted with DPAPI instead of plain text.
- UI available in multiple languages.

## Fastest Way to Run on Windows

1. Download the `I-Told-U-windows` package from the GitHub **Actions** or **Releases** tab.
2. Extract the ZIP.
3. Run:

```text
I-Told-U.exe
```

If Windows shows a SmartScreen warning, click **More info**, then **Run anyway**. That is normal for small unsigned apps.

## Run From Source on Windows

Requirements: Python 3.12.

```powershell
git clone https://github.com/szansky/itoldu.git
cd itoldu
copy .env.example .env
notepad .env
Set-ExecutionPolicy -Scope Process Bypass
.\run.ps1
```

Put your key in `.env`:

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

The `.env` file is ignored by git. Do not commit your real key.

## How To Use

1. Pick a microphone.
2. Click **Capture key** and press the exact key you want to use as the hotkey.
3. Leave **Paste to active window** enabled if you want the result inserted automatically.
4. Enable **Launch on Windows startup** and **Start minimized** if you want background behavior.
5. Turn off **DeepSeek translation** if you only want speech-to-text.
6. Turn on **DeepSeek translation** and choose a target language if you want translation.
7. Hold the hotkey, speak, then release it.

The default hotkey on first launch is `-`.

## Build Windows EXE

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\build_windows.ps1
```

The output is:

```text
dist\I-Told-U\I-Told-U.exe
```

## Linux

The Linux build is prepared too, but global hotkeys and clipboard injection may require extra permissions or packages depending on your desktop setup.

```bash
git clone https://github.com/szansky/itoldu.git
cd itoldu
cp .env.example .env
nano .env
bash build_linux.sh
```

The output is:

```text
dist/i-told-u/i-told-u
```

Helpful packages on Ubuntu:

```bash
sudo apt-get install portaudio19-dev python3-tk xclip xdotool
```

## DeepSeek API

Recommended format:

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

The app also supports the older name:

```env
DEEP_SEEK_API=your_deepseek_api_key_here
```

You can also paste the key into the app and click **Save key**. The field stays blank after restart so the secret is not shown on screen.

## Privacy

- The repository does not contain a real API key.
- `.env` and `.env.*` are ignored by git.
- The default `google` speech driver sends audio to Google Web Speech.
- Optional `whisper_local` runs locally, but uses more RAM:

```powershell
.\.venv\Scripts\python.exe -m pip install faster-whisper
```

## Troubleshooting

- Hotkey not responding: click **Capture key** again and save the settings.
- Same key on the left and right side of the keyboard: use **Capture key** so the app stores the physical scan code.
- Text is not pasted: check that **Paste to active window** is enabled.
- No translation: check `.env`, your API key, and whether **DeepSeek translation** is enabled.
- Microphone not picking up speech: choose a microphone from the list and refresh devices.

## Developer Commands

```powershell
.\.venv\Scripts\python.exe -m compileall app.py
.\.venv\Scripts\python.exe tools\render_assets.py
```

GitHub Actions builds Windows and Linux packages on every push to `main`.
