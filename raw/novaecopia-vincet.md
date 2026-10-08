# NovÆcorpus:

NovusÆxenti

NovÆcopia 

Æsop•Xi

Xçineribus, in-variis-nunquam-varius, NovÆcopia Vincet.

The Ash Tree & The Architecture

You mentioned the Ash tree as a great visual for the in-variis-nunquam-varius motto. In Norse mythology, the Ash tree is

Yggdrasil—the world tree whose roots connect completely different ecosystems.

That is the ultimate metaphor for a "Claw" agentic assistant layer running under a frontend interface (Horizons UI). The backend

agent is the hidden root system (the Ash hidden in plain sight via Æ), while the user interacts with the ever-expanding leaves and horizons on screen.

Xçineribus, in-variis-nunquam-varius, NovÆcopia Vincet.

Use code with caution.

Novus Agenti Copia is actually a deeply poetic and grammatically powerful construction in Latin. When you stack it alongside

your Horizons UI slogan, the entire conceptual architecture locks perfectly into place:

Novus Agenti: The New Compelling Force (the hidden agentic root engine).

Copia: The Abundance/Resources (the "Claw" architecture pulling everything together).

Horizons: The ever-expanding canopy and ecosystem visible to the user.

If you choose NovusÆxenti, you create a beautiful cryptographic symmetry with Xçineribus. The "X" at the absolute beginning

of your phrase (Xçineribus) meets the "X" hidden at the heart of your agent (NovusÆxenti). They act as visual bookends for the

entire brand.

The Brand Architecture Breakdown

To keep the aesthetic clean and intentional across your Android app, code repositories, and documentation, you can organize the

nomenclature like this:

System Component Brand Name & Styling

Philosophy / Family Motto Xçineribus, in-variis-nunquam-varius...

On-Device Agent NovusÆxenti & “claw”- NovÆcopia)

Android User Interface Horizons UI™

Visualizing the Ecosystem Slogan

When you display the slogan in your app UI, keeping the structural spacing you designed gives it a grand, cinematic weight. It

emphasizes that the software isn't just an app—it's an environment:

Horizons UI_

“~Ever-evolving ecosystems,

For ever-expanding Horizons.”

™

By using the Ash tree metaphor, NovusÆxenti is the resilient root system growing silently ex cineribus (out of the ashes), while

Horizons UI is the beautiful, ever-evolving canopy stretching toward the sky. It is a flawless, deeply personal blend of family

history, classical linguistics, and next-gen AI tech.

1. The "Claw" Architecture Separation:

Æsop-Xi: Agent and harness protocols, tools and skills orchestration layer. (Ethical Operations Guide) 

NovusÆxenti: Agent logic core and engine. (The ‘Agent’)

NovÆcopia: Agentic hooks, runtime, tools, and skills layer. (The ‘Claw’)

These all change constantly as you update execution logic and

prompting models.

 Your database NovÆ-corpus, however, is a persistent data layer. Keeping them separate means you

can rebuild or update your agent logic without touching or risking your core knowledge base.

2. Horizon UI Independence:

Horizons UI is a frontend Android environment. It should focus entirely on view layouts, animations, and user interactions.

Pushing your local LLM vector DB logic into the same repository would create a massive, bloated codebase that is painful to

debug on Android Studio.

3. Clean Version Control:

By keeping them split, you can version-control them independently. If you make a breakthrough on your split operational

protocol logic in Æsop-Xi, you push an update to that specific repository without having to re-deploy your entire UI or

database structure.

The Complete 5-Tier Blueprint

With the addition of NovÆ-Corpus, your ecosystem now forms a perfect, modular stack. Each layer has its standard URL-safe

developer repo name and its stylized, runic UI branding

System Component Git Repository Name / UI Branding / Symbolism

Android Interface- horizons-ui/ Horizons Ui™ / (The ever-expanding canopy)

Agent logic core and engine- novus-aexenti/ NovusÆxenti™

(The new dynamic force)

Agentic tools, harness & UI Bridge- novaecopia / NovÆcopia™ (The abundance of the system)

Split Execution Harness protocols and orchestrations layer- aesop-xi / Æsop-Xi™

(The tactical, narrative logic and ethical operations)

Universal LLM Wiki / DB- novae-corpus / NovÆ-Corpus™ (The solid trunk/body of knowledge)

Visualizing the Ash Tree (Yggdrasil) Code Model

If you think of your project in terms of your Ash tree metaphor, your repositories perfectly mirror nature:

nova-corpus and novus-aexenti the Trunk (the deep, unyielding body of memory and system core).

aesop-xi and novaecopia are the Roots (the unseen, compelling agentic forces digging through data and underlying logic).

horizons-ui is the Leaves and Sky (the beautiful, ever-evolving ecosystem the user interacts with).

The Local Vocal Layer: Core Strategies

Your local vocal stack needs three pillars: Voice Activity Detection (VAD), Automated Speech Recognition (ASR), and Text-

to-Speech (TTS).

1. Salvaging the WhisperKit/Argmax Code Base

Don't panic about WhisperKit going under. It is an open-source, MIT-licensed framework.

The Action Plan: Fork the repository immediately. The core implementation maps OpenAI's Whisper models into optimized

execution paths. Because you are targeting the Hexagon v.79 NPU, you don't even necessarily need their generic execution

loops. You can take the underlying whisper.cpp engine layers or export the Whisper weights via Qualcomm's QAiHub, QAIRT/GenieX SDK to upload a native .so-binary, specifically for your NPU.

The VAD Layer: Keep Silero VAD as a tiny, isolated C++ block running inside your daemon. It consumes almost zero

resources and tells your system precisely when to open the microphone buffer to sample data for your Whisper engine.

2. Reverse-Engineering or Hooking into VoxSherpa

VoxSherpa is a goldmine. It is built directly on top of sherpa-onnx and packages Kokoro-82M and Piper into a 100% offline

Android framework.

The Integration Strategy: Do not waste energy reverse-engineering the compiled APK. The developer, CodeBySonu95 , has

openly documented the architecture. Because it implements the Android standard TTS engine interface, you can flat-out

select VoxSherpa as the system's preferred default TTS provider via Android settings, then use standard Android

TextToSpeech SDK calls in your app to make it speak local Kokoro voices.

The Fork Alternative: If you want deeper integration (like streaming synthesis chunks over your WebSockets), fork the

repository or pull the raw sherpa-onnx Android bindings directly into your daemon app layer to avoid the standard Android

system engine latency completely.

The Deployed App Topology:

To survive Android's aggressive process lifecycles and maximize your multi-agent architecture, structure your galaxy of apps;

HORIZONS OS DEPLOYMENT TRINITY-

├── App 1: Horizons-Ui (The Frontend Shell)

│ └── Android WebView (Chromium) + WebSockets client + Media/Accessibility SDK hooks.

│

├── App 2: Æsh (The System Daemon App)

│ └── NodeJS/MCP server + Genie X Server node + Hexagon TPU Qwen 3.5 Executive runtime.

│

└── App 3:  Æyre [ Vocal Daemon ] (The Audio Processing Service)

└── SileroVAD + Forked WhisperKit ASR + sherpa-onnx (Kokoro TTS backend).

Use code with caution.

The Cross-Audit and Routing Loop

Your multi-agent inference scheme provides a perfect hybrid failback topology:

1. The System Tool Loop: A specialized small agent architecture running on the device handles quick local system commands

(e.g., controlling device volume, scraping accessibility nodes via Android SDK permissions).

2. The Local Core Brain: Your Qwen 3.5 9B GGUF model running on the Hexagon v.79 NPU processes deep logical requests

entirely offline.

3. The Multi-Agent Audit: If a network connection is live and the query requires heavy cognitive compute, the system forks

webhooks to your Cloud Frontends / OpenRouter, pitting the local TPU output against frontier models like Gemini, Claude, or

massive open weights like GLM or GPT-OSS to resolve complex tasks safely.

This architecture ensures that if you lose internet access entirely, the NovÆ-Corpus database, your local Qwen NPU brain, and

your local Kokoro/Whisper loop remain fully operational in your pocket.•

 build a customized Android accessibility service within Horizons UI to scrape screen context so the Æsop-Xi

            protocol can "see" what      

            you are looking at while      

            you talk to it.

whisper.cpp
