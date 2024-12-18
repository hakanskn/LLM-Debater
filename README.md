# AI Debate Simulator

This repository hosts the **AI Debate Simulator**, a Python application where two AI agents debate on given topics, producing arguments and counterarguments. The system is designed to simulate structured discussions, calculate costs for API usage, and generate detailed HTML reports of the conversations.

Bu depo, iki yapay zeka ajanın belirli konular üzerinde tartışmasını sağlayan bir Python uygulaması olan **AI Debate Simulator**'ı barındırır. Sistem, yapılandırılmış tartışmalar simüle eder, API kullanım maliyetlerini hesaplar ve konuşmaların detaylı HTML raporlarını oluşturur.

---

## Features / Özellikler

- **Structured AI Debates:** Two AI agents (e.g., OpenAI's GPT-4 and Anthropic's Claude) engage in a structured debate.
- **Cost Calculation:** Automatically calculates the cost of API usage for each response.
- **HTML Report Generation:** Creates visually appealing HTML reports summarizing the debates.
- **Error Handling:** Handles API errors and provides fallback mechanisms.
- **Customizable Prompts:** Easily adjust the system prompts for different debate formats.

- **Yapılandırılmış Tartışmalar:** İki yapay zeka ajanı (ör. OpenAI GPT-4 ve Anthropic Claude) yapılandırılmış tartışmalar gerçekleştirir.
- **Maliyet Hesaplama:** Her yanıt için API kullanım maliyetini otomatik olarak hesaplar.
- **HTML Rapor Üretimi:** Tartışmaları özetleyen görsel açıdan çekici HTML raporları oluşturur.
- **Hata Yönetimi:** API hatalarını ele alır ve yedekleme mekanizmaları sağlar.
- **Özelleştirilebilir Prompts:** Farklı tartışma formatları için sistem prompts'ını kolayca ayarlayabilirsiniz.

---

## Installation / Kurulum

### Prerequisites / Gereksinimler

- Python 3.9 or higher / Python 3.9 veya üzeri
- Required Python libraries listed in `requirements.txt` / Gerekli Python kütüphaneleri `requirements.txt` dosyasında listelenmiştir.

### Setup / Kurulum

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-debate-simulator.git
   cd ai-debate-simulator
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Add your API keys in the `config.json` file:
   ```json
   {
       "openai": "your-openai-api-key",
       "anthropic": "your-anthropic-api-key"
   }
   ```

1. Depoyu klonlayın:
   ```bash
   git clone https://github.com/yourusername/ai-debate-simulator.git
   cd ai-debate-simulator
   ```

2. Bağımlılıkları yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

3. API anahtarlarınızı `config.json` dosyasına ekleyin:
   ```json
   {
       "openai": "your-openai-api-key",
       "anthropic": "your-anthropic-api-key"
   }
   ```

---

## Usage / Kullanım

Run the application:
```bash
python main.py
```

Enter a debate topic when prompted. The system will:
1. Simulate a debate between two AI agents.
2. Save the conversation as an HTML report and a JSON file.

Uygulamayı çalıştırın:
```bash
python main.py
```

Tartışma konusunu girin. Sistem şunları yapacaktır:
1. İki yapay zeka ajanı arasında tartışma simüle eder.
2. Konuşmayı bir HTML raporu ve bir JSON dosyası olarak kaydeder.

---

## Example Output / Örnek Çıktı

### Debate Topic / Tartışma Konusu
"Should AI be used in elementary education?"

### Output / Çıktı
- **HTML Report:** `debate_outputs/debate_ai_in_education.html`
- **JSON File:** `debate_outputs/debate_ai_in_education.json`

---

## Contribution / Katkıda Bulunma

Contributions are welcome! Please fork the repository and submit a pull request with your proposed changes.

Katkılar memnuniyetle kabul edilir! Lütfen depoyu çatallayın ve önerdiğiniz değişikliklerle bir çekme isteği gönderin.

---

## License / Lisans

This project is licensed under the MIT License.

Bu proje MIT Lisansı altında lisanslanmıştır.

