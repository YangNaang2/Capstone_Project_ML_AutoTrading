# Capstone Project: Machine Learning for Automated Trading (UpBit)

**2024 Fall & 2025 Spring**

## 📌 Project Overview

This project focuses on implementing and optimizing **automated trading strategies** using **UpBit API**. Several traditional strategies are programmed and then backtested using the Python library **Backtrader** to assess their effectiveness. Additionally, machine learning models such as **LSTM (Long Short-Term Memory)** and **GRU (Gated Recurrent Units)** are used to predict price movements, with performance evaluations to determine their viability for trading.

The ultimate goal is to integrate the strategies with the UpBit API for real-time automated trading.

---

## 🔧 Technologies Used

- **Python**: Core programming language
- **UpBit API**: For integrating with the cryptocurrency exchange
- **Backtrader**: For backtesting trading strategies
- **LSTM**: A type of recurrent neural network for time-series predictions
- **GRU**: A variant of LSTM used for training on time-series data
- **TensorFlow**: For implementing LSTM/GRU models
- **Pandas**, **NumPy**, **Matplotlib**: For data manipulation and visualization

---

## ⚙️ Features

1. **Automated Trading**  
   - Integration with **UpBit API** for real-time market data and trading execution.

2. **Backtesting**  
   - Backtest multiple traditional trading strategies using **Backtrader** to evaluate their performance in historical data.

3. **Machine Learning Models**  
   - **LSTM** and **GRU** models to predict cryptocurrency price trends.
   - Evaluation of model performance and adjustment of hyperparameters.

4. **Real-Time Trading**  
   - Utilize the optimized strategies to execute live trades through the UpBit API.

---

## 🚀 Project Workflow

1. **Data Collection**  
   - Fetch historical price data using the **UpBit API**.
   - Clean and preprocess the data for use in machine learning models and backtesting.

2. **Strategy Implementation**  
   - Implement traditional trading strategies such as **Moving Averages**, **RSI**, etc.
   - Code various machine learning models like **LSTM** and **GRU** to predict price movements.

3. **Backtesting**  
   - Evaluate the effectiveness of each strategy through **Backtrader** by testing them on historical data.

4. **Model Training**  
   - Train the machine learning models using price data to forecast future trends and market directions.

5. **Real-Time Execution**  
   - Integrate the best-performing strategies with the UpBit API for **live trading**.

---

## 📈 Results & Evaluation

- **Backtesting Performance**  
  Evaluate the strategies based on key metrics like **Profit Factor**, **Sharpe Ratio**, and **Max Drawdown**.
  
- **Model Accuracy**  
  Measure the accuracy of machine learning models with metrics such as **Directional Accuracy**, **Mean Squared Error**, and **Theil's U-statistic**.

- **Real-Time Results**  
  Track the success rate of the trading bot using live market data and monitor its performance over time.

---

## 📝 Requirements

Before running the code, install the required libraries:

```bash
pip install -r requirements.txt
