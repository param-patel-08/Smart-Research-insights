"""
Babcock's 9 Strategic Themes with keywords for filtering and mapping
"""

BABCOCK_THEMES = {
    "Defense_Security": {
        "keywords": [
            "defense", "military", "surveillance", "threat detection", 
            "security systems", "radar", "sonar", "command control",
            "tactical systems", "weapons systems", "defense technology",
            "situational awareness", "force protection", "intelligence systems",
            "defense capability", "military technology", "combat systems"
        ],
        "strategic_priority": "HIGH",
        "description": "Defense and security systems for military applications"
    },
    
    "Autonomous_Systems": {
        "keywords": [
            "autonomous", "robot", "robotics", "UAV", "AUV", "UGV",
            "drone", "unmanned", "self-driving", "autonomous vehicle",
            "SLAM", "path planning", "navigation", "obstacle avoidance",
            "multi-agent", "swarm", "mobile robot", "manipulation",
            "autonomous navigation", "robotic system", "unmanned system"
        ],
        "strategic_priority": "HIGH",
        "description": "Autonomous systems and robotics for various domains"
    },
    
    "Cybersecurity": {
        "keywords": [
            "cybersecurity", "cyber security", "information security",
            "encryption", "cryptography", "network security", "malware",
            "vulnerability", "threat", "firewall", "intrusion detection",
            "zero-trust", "penetration testing", "security architecture",
            "cyber attack", "cyber defense", "security protocol",
            "information assurance", "data protection"
        ],
        "strategic_priority": "HIGH",
        "description": "Cybersecurity and information assurance"
    },
    
    "Energy_Sustainability": {
        "keywords": [
            "renewable energy", "solar", "wind", "battery", "energy storage",
            "hydrogen", "fuel cell", "grid", "power system", "sustainability",
            "carbon", "emission", "green energy", "photovoltaic",
            "energy efficiency", "microgrid", "smart grid", "clean energy",
            "energy transition", "decarbonization"
        ],
        "strategic_priority": "MEDIUM",
        "description": "Energy systems and sustainability technologies"
    },
    
    "Advanced_Manufacturing": {
        "keywords": [
            "additive manufacturing", "3D printing", "composite materials",
            "advanced materials", "metallurgy", "manufacturing process",
            "materials science", "carbon fiber", "lightweight materials",
            "fabrication", "materials characterization", "coating",
            "corrosion resistance", "structural materials", "metal alloy",
            "advanced composites"
        ],
        "strategic_priority": "MEDIUM",
        "description": "Advanced manufacturing and materials technologies"
    },
    
    "AI_Machine_Learning": {
        "keywords": [
            "artificial intelligence", "machine learning", "deep learning",
            "neural network", "computer vision", "natural language processing",
            "NLP", "reinforcement learning", "AI", "predictive model",
            "data analytics", "pattern recognition", "image recognition",
            "explainable AI", "federated learning", "transfer learning",
            "convolutional neural network", "recurrent neural network"
        ],
        "strategic_priority": "HIGH",
        "description": "AI and machine learning applications"
    },
    
    "Marine_Naval": {
        "keywords": [
            "marine", "naval", "ship", "submarine", "underwater",
            "ocean", "maritime", "vessel", "hydrodynamic", "marine engineering",
            "offshore", "subsea", "acoustic", "marine robotics",
            "ship design", "marine structures", "oceanography",
            "marine technology", "naval architecture", "underwater vehicle"
        ],
        "strategic_priority": "HIGH",
        "description": "Marine and naval technologies"
    },
    
    "Space_Aerospace": {
        "keywords": [
            "space", "satellite", "aerospace", "rocket", "orbital",
            "launch", "spacecraft", "aviation", "aeronautics",
            "space systems", "remote sensing", "space debris",
            "propulsion", "aerodynamic", "flight control",
            "space technology", "satellite system", "aerospace engineering"
        ],
        "strategic_priority": "MEDIUM",
        "description": "Space and aerospace systems"
    },
    
    "Digital_Transformation": {
        "keywords": [
            "IoT", "internet of things", "digital twin", "industry 4.0",
            "smart sensor", "edge computing", "5G", "cloud computing",
            "digital transformation", "sensor network", "wireless sensor",
            "industrial IoT", "smart manufacturing", "connectivity",
            "digitalization", "smart system"
        ],
        "strategic_priority": "MEDIUM",
        "description": "Digital transformation and IoT technologies"
    }
}

# Get all unique keywords for initial filtering
def get_all_keywords():
    """Get flattened list of all keywords across themes"""
    all_keywords = []
    for theme_data in BABCOCK_THEMES.values():
        all_keywords.extend(theme_data['keywords'])
    return list(set(all_keywords))

# Get themes by priority
def get_themes_by_priority(priority):
    """Get list of theme names with specific priority level"""
    return [
        theme_name for theme_name, data in BABCOCK_THEMES.items() 
        if data['strategic_priority'] == priority
    ]