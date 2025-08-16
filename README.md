# Kasanoma – Offline TTS Models for languages of Africa

**Kasanoma** is an open-source initiative dedicated to building and sharing **offline** **Text-to-Speech (TTS)** models for languages of Africa.  
With Kasanoma models, you can generate natural-sounding voices entirely on your local device — **no internet connection required**.

All models in this project are built using [Piper](https://github.com/rhasspy/piper), a fast, lightweight neural TTS system that runs efficiently on laptops, desktops, Raspberry Pi, and other low-resource devices.

You can also try out the models live online at our [demo site](https://kasanoma.onrender.com/). The models are trained for a limited amount of time due to GPU resource availability but they can be finetuned for better results using the training checkpoints which are also published.

---

## Available Models

We currently provide offline TTS models for the following languages:

| Language       | Main Countries                                              | Native Speakers | Total Speakers |
|----------------|-------------------------------------------------------------|-----------------|----------------|
| Twi (Akan) | Ghana                                                   | ~9–10 million   | ~17 million    |
| Chichewa   | Malawi, Zambia, Mozambique, Zimbabwe        | ~12 million     | ~18 million    |
| Makhuwa    | Mozambique                                              | ~7–8 million    | ~8 million     |


You can download the models from [releases](https://github.com/michsethowusu/kasanoma/releases).

> More African languages will be added soon.  
> **Languages in the pipeline:** Kikuyu, Tshiluba, Amharic, Vai.

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

If you have any questions or would like to contribute, our email is kasanoma@kasanoma.org.

---

## License

All Kasanoma models are released under open-source licenses.

