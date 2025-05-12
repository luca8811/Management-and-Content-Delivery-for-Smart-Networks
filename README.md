# Management-and-Content-Delivery-for-Smart-Networks
#LAB 1: Drone-Assisted Communication Network Simulation

This project simulates a smart urban Radio Access Network (RAN) enhanced with solar-powered UAVs acting as mobile base stations. The goal is to evaluate how UAVs can improve network performance during traffic peaks by offloading terrestrial base stations.

## 🔍 Features
- M/M/1 and M/M/m queuing models
- Configurable buffer sizes (infinite, finite, no buffer)
- Key metrics: packet loss, average delay, queue size, throughput
- Multi-server load balancing strategies (random, round robin, priority)
- Support for M/G/1 service time distribution

## 🛠 Technologies
- Python
- Event-driven simulation (queueMM1-ES.py)
- Matplotlib for performance visualization

## 📊 Some Metrics
- Average system delay
- Packet loss probability
- Server busy time
- Load distribution among antennas


#LAB 2: Drone Scheduling with Energy Constraints
This project extends the drone-assisted network simulation by introducing realistic energy constraints. Each UAV base station has limited battery life or solar-powered autonomy, and must be scheduled strategically to optimize traffic offloading.

## 🚁 Scenario
- Urban RAN with UAVs deployed during traffic peaks
- Drones powered by batteries and/or PV panels
- Time-dependent traffic profiles (Business vs Residential areas)
- Battery degradation modeled via charging/discharging cycles

## 🧪 Objectives
- Design scheduling strategies for drone deployment
- Evaluate performance across different battery types and PV capacities
- Analyze impact of energy limits on QoS and system efficiency
- Simulate multi-drone heterogeneous configurations (Type A, B, C)

## 📊 Key Metrics
- Traffic volume offloaded
- Battery cycle count
- Drone uptime and downtime
- Delay and queue metrics under different strategies

## 🛠 Technologies
- Python
- Custom event-based simulation engine
- Plotting with Matplotlib

