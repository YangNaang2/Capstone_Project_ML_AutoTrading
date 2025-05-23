![](https://github.com/YangNaang2/Capstone_Project_ML_AutoTrading/blob/main/Final_Code/screencapture-file-C-Users-Desktop-index-html-2025-05-06-14_25_30.png)

# Capstone Project:

## Machine Learning for Automated Trading (UPbit)

**2024 Fall & 2025 Spring**

## 📌 Project Overview

   여러 전통적인 거래 전략들을 프로그래밍하고, **Python 라이브러리인 Backtrader**를 이용해 백테스트를 진행하였음.<br> 
   LSTM (Long Short-Term Memory)과 GRU (Gated Recurrent Units)와 같은 머신러닝 모델을 사용하여 가격 변동 예측을 진행하였고,<br>
   그 성능을 평가하여 실제 거래에 적용할 수 있는지에 대한 가능성을 연구하였음.

최종적으로는 **UPbit API**를 활용해 실시간 거래 시스템을 구축하고, 자동매매를 실현하는 것이 목표.

---

## 🔧 사용된 기술

- **Python**: 핵심 프로그래밍 언어
- **UpBit API**: 암호화폐 거래소와 연동하기 위해 사용
- **Backtrader**: 거래 전략 백테스팅을 위한 라이브러리
- **LSTM**: 시계열 예측을 위한 순환 신경망 모델
- **GRU**: LSTM의 변형 모델로 시계열 데이터를 학습
- **TensorFlow**: LSTM/GRU 모델 구현을 위한 라이브러리
- **Pandas**, **NumPy**, **Matplotlib**: 데이터 처리 및 시각화

---

## ⚙️ 주요 기능

1. **자동화 거래**  
   - **UPbit API**와 연동하여 실시간 시장 데이터와 거래 실행을 처리.

2. **백테스팅**  
   - **Backtrader**를 사용해 여러 전통적인 거래 전략들을 백테스트하여 전략의 효율성을 평가.

3. **머신러닝 모델**  
   - **LSTM**과 **GRU** 모델을 활용하여 암호화폐 가격의 변동을 예측.
   - 모델 성능 평가 및 하이퍼파라미터 조정을 통한 최적화.

4. **실시간 거래**  
   - 백테스트에서 성과가 좋은 전략을 **UPbit API**와 연동하여 실시간으로 자동매매 실행.

---

## 🚀 프로젝트 흐름

- **2024년 10월**: **전략 공부**  
  - 전통적인 거래 전략들을 공부하여 투자에 대한 기초 지식을 배움.

- **2024년 11월**: **Backtrader 공부**  
  - **Backtrader** 라이브러리를 학습하고, 이를 활용한 백테스팅 방법을 익힘.

- **2025년 1월**: **사용할 전략 선택**  
  - 여러 전략을 분석하여 최종적으로 사용할 전략을 선택. 해당 전략들의 최적화를 진행함.

- **2025년 2월**: **여러 전략 구현 및 웹사이트 개설**  
  - 다양한 전략들을 코드로 구현. 웹사이트를 개설하여 보유한 전략들을 보여줄 수 있게 관리.

- **2025년 3월**: **GRU, LSTM 구현화**  
  - **GRU**와 **LSTM** 모델을 구현하여 암호화폐 가격 예측을 위한 모델을 학습하고 테스트.

---

## 📈 결과 및 평가

- **백테스팅 성과**  
  각 전략은 백테스트를 통해 실제 수익률을 바탕으로 평가되었음.
  전략들이 얼마나 효과적인지 **Profit Factor**, **Sharpe Ratio**, **Max Drawdown** 등을 기준으로 수익률을 계산.

- **모델 정확도**  
  **GRU**와 **LSTM** 모델을 통해 예측을 진행하였고, 상승과 하락을 맞추었는지 평가하는 **Directional Accuracy** 를 활용하여 머신러닝 모델의 성능을 평가.
  
- **실시간 성과**  
  실시간 거래에서 전략을 적용한 결과, 예상된 방향으로 가격 변동을 예측할 수 있었는지에 대한 성과를 추적하고 분석하였음.

---

file:///C:/Users/%EC%96%91%EC%A7%84%EC%9A%B0/Desktop/%EC%9E%90%EC%97%B0%EC%96%B4%EC%B2%98%EB%A6%AC/index.html
