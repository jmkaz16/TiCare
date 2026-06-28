# TiCare

This repository contains the software for **TiCare**, a robotics startup developed within the **IngenIA Robótica** framework of the Master's in Industrial Engineering (ETSII UPM). Our mission is to design healthcare robotics solutions for the home, focusing on companionship, assistance, and improving the quality of life for the elderly using the **TIAGo robot** platform.

Our ecosystem is divided into two distinct, fully functional robotic applications: the **TIAGo Robot Integration** (the main core) and the **Petoi Bittle Companion Robot**.

## TIAGo Robot Integration

The primary objective is to integrate advanced **SLAM navigation techniques in ROS 2** with **Computer Vision in Python** and **Natural Language Voice Control**. This system allows the **TIAGo robot** platform to autonomously locate, navigate toward, and retrieve objects in domestic environments to assist the elderly.

### System Demonstration

Watch and listen to TiCare in action. In this video, the user interacts with the TIAGo robot via voice commands to locate and retrieve objects:

<video src="media/demo.mp4" controls width="100%"></video>

> **Integration Status:** Full system integration across the TIAGo modules is near completion. Currently, this `main` branch includes the core architecture stable base merged with the `navigation` features.

### TIAGo Repository Structure & Branches
To maintain a clean workflow, development is divided into specialized branches managed by different teams. Each branch contains its own detailed `README.md` with specific installation instructions:
- [`main`](https://github.com/jmkaz16/TiCare/tree/main): The stable production branch, currently hosting the integrated baseline with `navigation` features.
- [`navigation`](https://github.com/jmkaz16/TiCare/tree/navigation): Core system for path planning, SLAM, map generation, and robot localization.
- [`vision`](https://github.com/jmkaz16/TiCare/tree/vision): AI perception algorithms, object detection, and camera frame processing.
- [`communication`](https://github.com/jmkaz16/TiCare/tree/communication): Core voice-interaction interface for TIAGo, processing user target requests and broadcasting robot text-to-speech locutions.

## Petoi Bittle Companion Robot

The repository also hosts the development for the **Petoi Bittle** robot. **This is an independent, fully functional standalone project** that runs outside the main TIAGo integration cycle.

It implements an advanced voice control system utilizing **Whisper and spaCy models** alongside a distributed ROS 2 node architecture to manage natural language commands, synonyms, and action queues.

- [`bittle`](https://github.com/jmkaz16/TiCare/tree/bittle): Contains the entire standalone codebase, architecture, and deployment instructions for the Petoi Bittle robot. Refer to its specific `README.md` inside that branch for setup details.

## Team Members
- **Daniel Franco** – CEO & Requirements Manager
- **Luis Gómez** – CTO & Product Manager
- **Marco Muñoz** – Design & Modeling Manager
- **Catalina Morán** – Construction & Test Manager
- **Juan Martínez** – Project, Documentation & Tool Manager
- **Nour Maimouni** – Communication & Liaisons Manager
- **Mario Guerra** – Simulation & Control Manager
- **Lucas Goñi** – Assurance, Quality, Impact & Sustainability Manager

## Documentation & Links
- 📖 Detailed Technical Docs: [TiCare Navigation on GitHub Pages](https://jmkaz16.github.io/TiCare/)
- 🌐 Web: [www.ticare.com](https://new-chat-n7ld.bolt.host/)
- 📸 Instagram: [@TiCare\_\_](https://instagram.com/TiCare__)
- 📧 Email: [ticare.ingenia@gmail.com](mailto:ticare.ingenia@gmail.com)
- 📍 Ubicación: [ETSII UPM](https://maps.app.goo.gl/VJqcJQks2CgoceWcA)
