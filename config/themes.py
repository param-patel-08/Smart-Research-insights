"""
Babcock's 9 Strategic Themes with keywords for filtering and mapping
"""

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