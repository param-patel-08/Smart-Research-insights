# Changes Restored + Keyword Expansion

## ✅ All Changes Restored

### 1. run_full_analysis.py - Collection Parameters Fixed
**Restored optimized collection limits:**
- Quick test: 50 → **500 papers/theme** (min_relevance=0.3)
- Medium test: 100 → **2,000 papers/theme** (min_relevance=0.25)
- Full collection: 500 → **10,000 papers/theme** (min_relevance=0.2)

### 2. src/theme_based_collector.py - Query Strategy Fixed
**Removed restrictive AND operator:**
- Before: `(theme keywords) AND (engineering OR technology...)`
- After: `theme keywords only`
- Increased top_n_keywords: 15 → **30** for better coverage

### 3. config/themes.py - Keywords EXPANDED

#### Cybersecurity (was 18 → now 50+ keywords)
**Added:**
- authentication, access control, security system, cyber threat, ransomware, phishing, DDoS
- secure communication, PKI, SSL, TLS, security assessment, risk management, incident response
- security monitoring, threat intelligence, endpoint security, cloud security, application security
- security testing, security audit, compliance, privacy, GDPR, security framework
- NIST, ISO 27001, security operations, SOC, SIEM, threat hunting, forensics, security analytics

#### Energy_Sustainability (was 20 → now 52+ keywords)
**Added:**
- solar panel, wind turbine, energy management, power generation, energy conversion
- electric vehicle, EV, charging infrastructure, lithium battery, energy harvesting
- thermal energy, geothermal, biomass, hydroelectric, tidal energy, wave energy, ocean energy
- energy policy, net zero, carbon neutral, carbon capture, CCUS, energy sector
- sustainable energy, alternative energy, power electronics, inverter, converter
- energy optimization, demand response, load balancing, grid integration, distributed generation
- renewable integration, energy resilience, power quality

#### Advanced_Manufacturing (was 16 → now 50+ keywords)
**Added:**
- manufacturing technology, industrial process, CNC, machining, automation, production, assembly
- quality control, process optimization, lean manufacturing, smart manufacturing, factory
- production line, tooling, welding, joining, surface treatment, heat treatment
- polymer, ceramic, nanomaterial, nanocomposite, mechanical properties, material testing
- fatigue, fracture, finite element, FEA, CAD, CAM, digital manufacturing
- cyber-physical system, advanced welding, laser processing, material processing
- powder metallurgy, casting, forging

#### AI_Machine_Learning (was 18 → now 56+ keywords)
**Added:**
- CNN, RNN, LSTM, GAN, generative adversarial network, transformer, BERT, GPT
- large language model, LLM, supervised learning, unsupervised learning, semi-supervised
- classification, regression, clustering, anomaly detection, object detection
- semantic segmentation, instance segmentation, speech recognition, text mining, sentiment analysis
- recommendation system, decision tree, random forest, support vector machine, SVM
- gradient boosting, XGBoost, AutoML, neural architecture search, hyperparameter optimization
- model training, model deployment, ML pipeline, MLOps, feature engineering, data preprocessing
- model evaluation, edge AI, TinyML, on-device ML, AI accelerator, TPU, GPU computing

## Expected Improvements

### Before Keyword Expansion:
| Theme | Papers Collected | Issue |
|-------|------------------|-------|
| Cybersecurity | 420 | Too few |
| Energy | 11 | Way too few |
| Manufacturing | 6 | Way too few |
| AI/ML | 24 | Way too few |

### After Keyword Expansion (Expected):
| Theme | Expected Papers | Improvement |
|-------|----------------|-------------|
| Cybersecurity | 2,000-3,000 | 5-7x increase ✅ |
| Energy | 1,000-2,000 | 100x increase ✅ |
| Manufacturing | 1,000-1,500 | 250x increase ✅ |
| AI/ML | 2,000-3,000 | 100x increase ✅ |

### Total Expected Papers (Full Collection):
- **Before**: ~12,500 papers (imbalanced themes)
- **After**: **20,000-30,000 papers** (balanced coverage)

## Next Steps

Run the full analysis again:
```bash
python run_full_analysis.py 3
```

This should now:
1. ✅ Collect 10,000 papers per theme (not limited by narrow queries)
2. ✅ Get good coverage for all themes (not just Defense/Marine/Aerospace)
3. ✅ Apply relevance filtering (0.2 threshold keeps ~50%)
4. ✅ Result in 20,000-30,000 Babcock-relevant papers

The expanded keywords ensure Australasian universities' papers in Energy, Manufacturing, Cybersecurity, and AI/ML are captured!
