"""
Babcock's 9 Strategic Themes with Hierarchical Sub-themes
Enhanced structure for better emerging topic detection and trend analysis

Structure:
- 9 Strategic Themes (Level 1) - Executive reporting
- 40 Sub-themes (Level 2) - Detailed analysis & trends
- ~60 BERTopic Topics (Level 3) - Deep dive & emerging topics
"""

# Hierarchical theme structure with sub-themes
BABCOCK_THEMES_HIERARCHICAL = {
    "AI_Machine_Learning": {
        "sub_themes": {
            "Computer_Vision": [
                "computer vision", "image recognition", "object detection", "facial recognition",
                "semantic segmentation", "instance segmentation", "pose estimation", "activity recognition",
                "image classification", "optical character recognition", "OCR", "scene understanding",
                "visual recognition", "image processing", "video analysis", "3D vision"
            ],
            "Natural_Language_Processing": [
                "natural language processing", "NLP", "text mining", "sentiment analysis",
                "chatbot", "dialogue system", "question answering", "information extraction",
                "named entity recognition", "NER", "language model", "BERT", "GPT",
                "transformer", "large language model", "text classification", "machine translation",
                "speech recognition", "text generation"
            ],
            "Reinforcement_Learning": [
                "reinforcement learning", "RL", "deep reinforcement learning", "Q-learning",
                "policy gradient", "actor-critic", "multi-agent learning", "game AI",
                "robot learning", "autonomous agent"
            ],
            "Explainable_AI": [
                "explainable AI", "interpretable", "XAI", "model interpretability",
                "feature importance", "SHAP", "LIME", "attention mechanism",
                "model transparency", "AI ethics", "fairness", "bias"
            ],
            "AI_Hardware_Acceleration": [
                "edge AI", "TinyML", "on-device ML", "AI accelerator", "TPU",
                "GPU computing", "model compression", "quantization", "knowledge distillation",
                "pruning", "neural architecture search", "AutoML", "MLOps"
            ]
        },
        "strategic_priority": "HIGH",
        "description": "AI and machine learning applications"
    },
    
    "Defense_Security": {
        "sub_themes": {
            "Military_Systems": [
                "weapons systems", "weapon", "missile", "combat systems", "radar", "sonar",
                "defense technology", "defence technology", "tactical systems", "warfighting",
                "electronic warfare", "countermeasure", "anti-submarine"
            ],
            "Strategic_Defense": [
                "defense", "defence", "military", "armed forces", "command control",
                "command and control", "situational awareness", "force protection",
                "strategic deterrence", "mission planning", "c4isr", "joint operations"
            ],
            "Border_Security": [
                "border security", "homeland security", "coastal defence", "maritime security",
                "surveillance", "threat detection", "security systems", "sea control"
            ],
            "Intelligence_Operations": [
                "intelligence systems", "intelligence", "national security", "security policy",
                "threat intelligence", "information warfare", "cyber defense"
            ]
        },
        "strategic_priority": "HIGH",
        "description": "Defense and security systems for military applications"
    },
    
    "Autonomous_Systems": {
        "sub_themes": {
            "Autonomous_Vehicles": [
                "autonomous vehicle", "self-driving", "autonomous car", "autonomous driving",
                "vehicle automation", "ADAS", "connected vehicle"
            ],
            "Drones_UAVs": [
                "UAV", "drone", "unmanned aerial", "quadcopter", "aerial robot",
                "UAV navigation", "drone system"
            ],
            "Robot_Navigation": [
                "SLAM", "path planning", "navigation", "obstacle avoidance", "localization",
                "mapping", "autonomous navigation", "mobile robot", "robot perception"
            ],
            "Swarm_Intelligence": [
                "multi-agent", "swarm", "swarm robot", "cooperative robot", "robot coordination",
                "distributed robot", "collective behavior"
            ]
        },
        "strategic_priority": "HIGH",
        "description": "Autonomous systems and robotics for various domains"
    },
    
    "Cybersecurity": {
        "sub_themes": {
            "Network_Security": [
                "network security", "firewall", "intrusion detection", "intrusion prevention",
                "VPN", "network defense", "perimeter security", "DDoS", "network attack"
            ],
            "Cryptography": [
                "cryptography", "encryption", "PKI", "SSL", "TLS", "digital signature",
                "cryptographic protocol", "hash function", "cipher"
            ],
            "Threat_Detection": [
                "threat detection", "malware", "vulnerability", "threat", "ransomware",
                "phishing", "threat intelligence", "threat hunting", "security analytics",
                "anomaly detection", "intrusion detection"
            ],
            "Zero_Trust": [
                "zero-trust", "zero trust", "access control", "authentication",
                "identity management", "least privilege", "micro-segmentation"
            ],
            "Quantum_Cryptography": [
                "quantum cryptography", "post-quantum", "quantum security",
                "quantum key distribution", "quantum-resistant"
            ]
        },
        "strategic_priority": "HIGH",
        "description": "Cybersecurity and information assurance"
    },
    
    "Energy_Sustainability": {
        "sub_themes": {
            "Renewable_Energy": [
                "renewable energy", "solar", "wind", "photovoltaic", "solar panel",
                "wind turbine", "clean energy", "green energy", "sustainable energy",
                "alternative energy", "hydroelectric", "tidal energy", "wave energy",
                "ocean energy", "geothermal", "biomass"
            ],
            "Energy_Storage": [
                "battery", "energy storage", "lithium battery", "fuel cell", "hydrogen",
                "supercapacitor", "battery management", "energy density", "charging"
            ],
            "Smart_Grids": [
                "grid", "smart grid", "microgrid", "power system", "grid integration",
                "distributed generation", "demand response", "load balancing",
                "grid stability", "power quality", "renewable integration"
            ],
            "Carbon_Capture": [
                "carbon", "emission", "carbon capture", "CCUS", "carbon neutral",
                "net zero", "decarbonization", "carbon reduction", "greenhouse gas"
            ]
        },
        "strategic_priority": "MEDIUM",
        "description": "Energy systems and sustainability technologies"
    },
    
    "Advanced_Manufacturing": {
        "sub_themes": {
            "Additive_Manufacturing_3D_Printing": [
                "additive manufacturing", "3D printing", "rapid prototyping", "SLS", "SLA",
                "FDM", "metal 3D printing", "polymer printing", "bio-printing",
                "layer-by-layer", "print process"
            ],
            "Industrial_Robotics": [
                "industrial robot", "robot", "robotics", "robotic arm", "manipulation",
                "pick and place", "assembly robot", "collaborative robot", "cobot"
            ],
            "Smart_Manufacturing": [
                "smart manufacturing", "industry 4.0", "digital manufacturing", "factory",
                "production line", "automation", "cyber-physical system", "manufacturing process"
            ],
            "Advanced_Materials": [
                "composite materials", "advanced materials", "carbon fiber", "lightweight materials",
                "metallurgy", "materials science", "metal alloy", "advanced composites",
                "nanomaterial", "nanocomposite", "polymer", "ceramic"
            ],
            "Manufacturing_Automation": [
                "CNC", "machining", "automation", "production", "process optimization",
                "lean manufacturing", "quality control", "tooling", "CAD", "CAM"
            ]
        },
        "strategic_priority": "MEDIUM",
        "description": "Advanced manufacturing and materials technologies"
    },
    
    "Marine_Naval": {
        "sub_themes": {
            "Naval_Systems": [
                "naval", "navy", "ship", "submarine", "vessel", "naval warfare",
                "naval architecture", "ship design", "warship"
            ],
            "Ocean_Engineering": [
                "marine engineering", "ocean engineering", "offshore", "subsea",
                "marine structures", "oceanography", "marine technology"
            ],
            "Marine_Robotics": [
                "marine robotics", "underwater vehicle", "AUV", "ROV", "underwater robot",
                "marine robot", "ocean robot"
            ],
            "Underwater_Vehicles": [
                "underwater", "subsea vehicle", "submersible", "underwater navigation",
                "underwater communication", "acoustic", "sonar"
            ]
        },
        "strategic_priority": "HIGH",
        "description": "Marine and naval technologies"
    },
    
    "Space_Aerospace": {
        "sub_themes": {
            "Satellites": [
                "satellite", "satellite system", "remote sensing", "Earth observation",
                "satellite communication", "satellite navigation", "GPS", "orbit"
            ],
            "Space_Systems": [
                "space systems", "spacecraft", "space technology", "space mission",
                "space debris", "orbital", "launch"
            ],
            "Propulsion": [
                "propulsion", "rocket", "engine", "thrust", "combustion",
                "electric propulsion", "ion propulsion"
            ],
            "Space_Exploration": [
                "space exploration", "space station", "lunar", "Mars", "planetary",
                "deep space", "space colonization"
            ],
            "Aerospace_Materials": [
                "aerospace", "aeronautics", "aviation", "aerodynamic", "flight control",
                "aerospace engineering", "aircraft", "airframe"
            ]
        },
        "strategic_priority": "MEDIUM",
        "description": "Space and aerospace systems"
    },
    
    "Digital_Transformation": {
        "sub_themes": {
            "Digital_Twin": [
                "digital twin", "virtual model", "simulation model", "cyber-physical",
                "virtual replica", "digital replica"
            ],
            "IoT_Industry40": [
                "IoT", "internet of things", "industry 4.0", "smart sensor", "sensor network",
                "wireless sensor", "industrial IoT", "IIoT", "connected device"
            ],
            "Cloud_Computing": [
                "cloud computing", "cloud", "edge computing", "fog computing",
                "distributed computing", "cloud infrastructure", "cloud service"
            ],
            "Business_Analytics": [
                "digital transformation", "digitalization", "business intelligence",
                "data analytics", "predictive analytics", "business analytics", "dashboard"
            ]
        },
        "strategic_priority": "MEDIUM",
        "description": "Digital transformation and IoT technologies"
    }
}

# Legacy flat structure for backward compatibility
BABCOCK_THEMES = {
    "Defense_Security": {
        "keywords": [
            "defense", "defence", "military", "armed forces", "surveillance",
            "threat detection", "security systems", "radar", "sonar",
            "command control", "command and control", "tactical systems",
            "weapons systems", "weapon", "missile", "defense technology",
            "defence technology", "situational awareness", "force protection",
            "intelligence systems", "intelligence", "national security",
            "security policy", "military operations", "warfighting",
            "combat systems", "combat capability", "defense industry",
            "defence industry", "maritime security", "naval warfare",
            "navy", "air force", "army", "joint operations",
            "c4isr", "electronic warfare", "countermeasure", "battlefield",
            "strategic deterrence", "homeland security", "coastal defence",
            "border security", "anti-submarine", "ship defence",
            "sea control", "mission planning"
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
            "information assurance", "data protection", "authentication",
            "access control", "security system", "cyber threat", "ransomware",
            "phishing", "DDoS", "secure communication", "PKI", "SSL", "TLS",
            "security assessment", "risk management", "incident response",
            "security monitoring", "threat intelligence", "endpoint security",
            "cloud security", "application security", "security testing",
            "security audit", "compliance", "privacy", "GDPR",
            "security framework", "NIST", "ISO 27001", "security operations",
            "SOC", "SIEM", "threat hunting", "forensics", "security analytics"
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
            "energy transition", "decarbonization", "solar panel", "wind turbine",
            "energy management", "power generation", "energy conversion",
            "electric vehicle", "EV", "charging infrastructure", "lithium battery",
            "energy harvesting", "thermal energy", "geothermal", "biomass",
            "hydroelectric", "tidal energy", "wave energy", "ocean energy",
            "energy policy", "net zero", "carbon neutral", "carbon capture",
            "CCUS", "energy sector", "sustainable energy", "alternative energy",
            "power electronics", "inverter", "converter", "energy optimization",
            "demand response", "load balancing", "grid integration", "distributed generation",
            "renewable integration", "energy resilience", "power quality"
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
            "advanced composites", "manufacturing technology", "industrial process",
            "CNC", "machining", "automation", "production", "assembly",
            "quality control", "process optimization", "lean manufacturing",
            "smart manufacturing", "factory", "production line", "tooling",
            "welding", "joining", "surface treatment", "heat treatment",
            "polymer", "ceramic", "nanomaterial", "nanocomposite",
            "mechanical properties", "material testing", "fatigue", "fracture",
            "finite element", "FEA", "CAD", "CAM", "digital manufacturing",
            "cyber-physical system", "advanced welding", "laser processing",
            "material processing", "powder metallurgy", "casting", "forging"
        ],
        "strategic_priority": "MEDIUM",
        "description": "Advanced manufacturing and materials technologies"
    },
    
    "AI_Machine_Learning": {
        "keywords": [
            # Core AI/ML terms
            "artificial intelligence", "machine learning", "deep learning",
            "neural network", "computer vision", "natural language processing",
            "reinforcement learning", "predictive model", "predictive analytics",
            "data analytics", "pattern recognition", "image recognition",
            "explainable AI", "federated learning", "transfer learning",
            
            # Neural architectures
            "convolutional neural network", "recurrent neural network",
            "CNN", "RNN", "LSTM", "GAN", "generative adversarial network",
            "transformer", "BERT", "GPT", "large language model",
            "attention mechanism", "ResNet", "VGG", "AlexNet", "U-Net",
            
            # ML techniques
            "supervised learning", "unsupervised learning", "semi-supervised",
            "classification", "regression", "clustering", "anomaly detection",
            "object detection", "semantic segmentation", "instance segmentation",
            "speech recognition", "text mining", "sentiment analysis",
            "recommendation system", "decision tree", "random forest",
            "support vector machine", "SVM", "gradient boosting", "XGBoost",
            "k-means", "ensemble learning", "bagging", "boosting",
            
            # ML tools/frameworks
            "TensorFlow", "PyTorch", "Keras", "scikit-learn", "OpenCV",
            "YOLO", "Mask R-CNN", "EfficientNet", "MobileNet",
            
            # ML pipeline & ops
            "AutoML", "neural architecture search", "hyperparameter optimization",
            "model training", "model deployment", "ML pipeline", "MLOps",
            "feature engineering", "data preprocessing", "model evaluation",
            "cross-validation", "overfitting", "regularization",
            
            # Edge/Mobile AI
            "edge AI", "TinyML", "on-device ML", "AI accelerator",
            "TPU", "GPU computing", "model compression", "quantization",
            "knowledge distillation", "pruning",
            
            # Application areas (make it more specific)
            "facial recognition", "pose estimation", "activity recognition",
            "image classification", "image segmentation", "optical character recognition",
            "OCR", "chatbot", "dialogue system", "question answering",
            "information extraction", "named entity recognition", "NER",
            "time series forecasting", "predictive maintenance"
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

# ==================== HIERARCHICAL THEME HELPERS ====================

def get_all_sub_themes():
    """Get flat dictionary mapping sub-theme names to their keywords"""
    sub_themes = {}
    for parent_theme, theme_data in BABCOCK_THEMES_HIERARCHICAL.items():
        for sub_theme_name, keywords in theme_data['sub_themes'].items():
            sub_themes[sub_theme_name] = {
                'parent_theme': parent_theme,
                'keywords': keywords,
                'priority': theme_data['strategic_priority']
            }
    return sub_themes

def get_sub_themes_for_parent(parent_theme):
    """Get list of sub-theme names for a given parent theme"""
    if parent_theme in BABCOCK_THEMES_HIERARCHICAL:
        return list(BABCOCK_THEMES_HIERARCHICAL[parent_theme]['sub_themes'].keys())
    return []

def get_parent_theme(sub_theme):
    """Get parent theme name for a given sub-theme"""
    for parent, theme_data in BABCOCK_THEMES_HIERARCHICAL.items():
        if sub_theme in theme_data['sub_themes']:
            return parent
    return None

def get_all_hierarchical_keywords():
    """Get flattened list of all keywords from hierarchical structure"""
    all_keywords = []
    for theme_data in BABCOCK_THEMES_HIERARCHICAL.values():
        for keywords in theme_data['sub_themes'].values():
            all_keywords.extend(keywords)
    return list(set(all_keywords))

def count_themes():
    """Return counts of themes at each level"""
    parent_count = len(BABCOCK_THEMES_HIERARCHICAL)
    sub_theme_count = sum(len(data['sub_themes']) for data in BABCOCK_THEMES_HIERARCHICAL.values())
    return {
        'parent_themes': parent_count,
        'sub_themes': sub_theme_count,
        'total_hierarchical': parent_count + sub_theme_count
    }

# TEMPORARY TEST: Validate hierarchical structure
def _test_hierarchical_structure():
    """TEMPORARY: Test function to validate the hierarchical theme structure"""
    counts = count_themes()
    print(f"Theme Structure:")
    print(f"  Parent Themes: {counts['parent_themes']}")
    print(f"  Sub-themes: {counts['sub_themes']}")
    print(f"  Total: {counts['total_hierarchical']}")
    print(f"\nSub-themes per parent:")
    for parent in BABCOCK_THEMES_HIERARCHICAL:
        sub_count = len(get_sub_themes_for_parent(parent))
        print(f"  {parent}: {sub_count} sub-themes")
    
if __name__ == "__main__":
    # TEMPORARY: Run validation when file is executed directly
    _test_hierarchical_structure()