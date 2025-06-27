# 🧠 Decarbon AI Master Brain

A modular, agent-oriented decarbonization AI system for real-time energy management and optimization.

## 🚀 **System Status: FULLY OPERATIONAL**

✅ **Dashboard**: Running at `http://localhost:8501`  
✅ **Chatbot**: Running at `http://localhost:8502`  
✅ **Core System**: All agents communicating and processing data  
✅ **Data Generation**: Realistic energy data being simulated in real-time  

## 🎯 **What's Working Right Now**

### **Real-time Dashboard**
- ⚡ Live energy flow visualization (Sankey diagram)
- 📊 Current metrics (solar, load, battery, grid price, CO₂)
- 🤖 AI decision display
- 🚨 Alert system
- 🏗️ Infrastructure recommendations
- 📈 24-hour energy trends

### **AI Chatbot Interface**
- 💬 Interactive chat with energy management AI
- 📊 Real-time system status in sidebar
- ⚡ Quick action buttons for common queries
- 📈 Chat statistics and history
- 🎯 Contextual responses about energy optimization

### **Core System**
- 🔄 Real-time data ingestion and processing
- 📊 Energy forecasting and load prediction
- 🤖 AI-powered decision making
- ⚡ State management and simulation
- 📝 Comprehensive logging

## 🛠️ **Architecture**

```
Decarbon_day/
├── agents/           # AI agents (ingestion, forecast, decision, etc.)
├── core/            # Core system modules (state, scheduler, logger)
├── dashboard/       # Streamlit dashboard interface
├── chatbot/         # Streamlit chatbot interface
├── data/           # Data files and CSV storage
├── utils/          # Utilities (data processing, LLM integration)
└── main.py         # System entry point
```

## 🚀 **Quick Start**

### **1. View the Dashboard**
```bash
streamlit run dashboard/app.py
```
Open: `http://localhost:8501`

### **2. Chat with AI Assistant**
```bash
streamlit run chatbot/interface.py
```
Open: `http://localhost:8502`

### **3. Run Full System**
```bash
python main.py --test
```

## 📊 **Live Data Stream**

The system generates realistic energy data:
- **Solar Generation**: 0-30 kWh (day/night cycle)
- **Load Consumption**: 20-165 kWh (variable demand)
- **Grid Price**: €0.13-0.23/kWh (dynamic pricing)
- **CO₂ Intensity**: 325-460 g/kWh (grid carbon intensity)
- **Battery SOC**: 55-65% (realistic cycling)

## 🎯 **Features**

### **Dashboard Features**
- Real-time energy flow visualization
- Live metrics and KPIs
- AI decision tracking
- Alert management
- Infrastructure recommendations
- Historical trends

### **Chatbot Features**
- Natural language energy queries
- Real-time system status
- Optimization recommendations
- Infrastructure upgrade advice
- CO₂ impact analysis
- Quick action buttons

### **AI Capabilities**
- Energy load forecasting
- Solar generation prediction
- Grid price optimization
- Battery management
- Infrastructure recommendations
- CO₂ reduction strategies

## 🔧 **Configuration**

### **Environment Variables**
Create a `.env` file:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

### **Dependencies**
All required packages are installed:
- `streamlit==1.12.0`
- `altair==4.2.2`
- `pandas==2.1.0`
- `numpy==1.24.0`
- `google-generativeai==0.3.0`
- `plotly==5.17.0`
- And more...

## 🎨 **Demo Mode**

The system currently runs in **demo mode** with:
- ✅ Realistic simulated data
- ✅ Full UI functionality
- ✅ Mock AI responses
- ✅ Complete visualization

**To enable full AI functionality:**
1. Add your Gemini API key to `.env`
2. Restart the applications
3. Enjoy full AI-powered responses!

## 📈 **Performance**

- **Real-time Updates**: Every 5 seconds
- **Data Accuracy**: Realistic energy patterns
- **Response Time**: <1 second for UI updates
- **Scalability**: Modular agent architecture

## 🌱 **Sustainability Impact**

The system helps:
- **Reduce Energy Costs**: Smart load management
- **Lower CO₂ Emissions**: Solar optimization
- **Improve Efficiency**: AI-driven decisions
- **Plan Upgrades**: Data-driven recommendations

## 🔮 **Next Steps**

1. **Add Real API Key**: Enable full AI functionality
2. **Connect Real Sensors**: Replace simulated data
3. **Customize Alerts**: Set up your specific thresholds
4. **Scale Up**: Add more energy sources and loads

---

**🎉 Your Decarbon AI Master Brain is ready to optimize your energy system!** 