# Kasanoma – Offline TTS Models for Ghanaian Languages

**Kasanoma** is an open-source initiative dedicated to building and sharing **offline** high-quality **Text-to-Speech (TTS)** models for Ghanaian languages.  
With Kasanoma, you can generate natural-sounding Ghanaian voices entirely on your local device — **no internet connection required**.

All models in this project are built using [Piper](https://github.com/rhasspy/piper), a fast, lightweight neural TTS system that runs efficiently on laptops, desktops, Raspberry Pi, and other low-resource devices.

You can also try out the models live online at our [demo site](https://kasanoma.onrender.com/).

---

## Available Models

Currently, we provide models for **Twi (Akan)**:
You can download them from the [releases](https://github.com/michsethowusu/kasanoma/releases).

> More Ghanaian languages will be added soon — including Ewe, Ga, Dagbani, and others.  
> We welcome community contributions.

---

## How to Use the Models Offline

All Kasanoma models are compatible with [Piper](https://github.com/rhasspy/piper).  
Here’s how to run them without internet access:

1. **Install Piper**  
   You can install it via pip:
   ```bash
   pip install piper-tts
   ```
   Or download a standalone binary from the [Piper releases page](https://github.com/rhasspy/piper/releases) for your platform (Linux, macOS, Windows).

2. **Download a Kasanoma Model**  
   Get the `.onnx` model file and its matching `.json` config file for your language.

3. **Run TTS**  
   ```bash
   piper --model kasanoma-twi-medium.onnx --output audio.wav <<EOF
   Me pɛ sɛ me kɔ sukuu no mu.
   EOF
   ```
   This will generate `audio.wav` with natural Twi speech — fully offline.


---

## Contributing

We welcome:  
- New TTS voices for Ghanaian languages  
- Improved datasets and phoneme dictionaries  
- Audio quality testing and pronunciation feedback  

To contribute, please open an issue or submit a pull request.

---

## License

All Kasanoma models are released under open-source licenses.

