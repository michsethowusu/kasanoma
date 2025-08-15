# Kasanoma – Offline TTS Models for languages of Africa

**Kasanoma** is an open-source initiative dedicated to building and sharing **offline** high-quality **Text-to-Speech (TTS)** models for languages of Africa.  
With Kasanoma models, you can generate natural-sounding voices entirely on your local device — **no internet connection required**.

All models in this project are built using [Piper](https://github.com/rhasspy/piper), a fast, lightweight neural TTS system that runs efficiently on laptops, desktops, Raspberry Pi, and other low-resource devices.

You can also try out the models live online at our [demo site](https://kasanoma.onrender.com/).

---

## Available Models

## Currently Supported Languages

- **Twi (Akan)** — spoken mainly in **Ghana**, by about **9–10 million** native speakers and over **17 million** total speakers.  
- **Chichewa** — spoken mainly in **Malawi**, **Zambia**, **Mozambique**, and **Zimbabwe**, by about **12 million** native speakers and over **18 million** total speakers.

You can download the models from [releases](https://github.com/michsethowusu/kasanoma/releases).

> More African languages will be added soon.  
> **Languages in the pipeline:** Makhuwa — spoken mainly in **Mozambique**, by about **8 million** speakers.

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

We welcome contributions in the form of:  
- Training new models for other languages of Africa or finetuning the released models. All the knowledge from training models is open source and will be shared freely to support you.  
- Audio quality testing and pronunciation feedback.
- Add scripts for using the models offline

To contribute, you can make a pull request, post in the issues or contact me on [LinkedIn](https://www.linkedin.com/in/mich-seth-owusu).

---

## License

All Kasanoma models are released under open-source licenses.

