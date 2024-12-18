import openai
from anthropic import Anthropic
import time
from datetime import datetime
import json
import os
from config_manager import ConfigManager
from cost_calculator import CostCalculator


class DebateSimulator:
    def __init__(self):

        # Hata sayaçları ekle
        self.chatgpt_errors = 0
        self.claude_errors = 0
        self.max_errors = 3

        # Completion kontrolü için son karakterler
        self.ending_chars = ['.', '!', '?']

        # Özel bitiş tokeni
        self.agreement_token = "##TARTISMA_SONU##"

        # HTML template'i r-string olarak tanımla ve style'ı ayrı tut
        self.CSS_STYLE = """
        body { 
            font-family: Arial, sans-serif; 
            max-width: 800px; 
            margin: 0 auto; 
            padding: 20px; 
            background-color: #f5f5f5; 
        }
        .message { 
            margin: 10px 0; 
            padding: 15px; 
            border-radius: 10px; 
            max-width: 80%; 
        }
        .chatgpt { 
            background-color: #e9f5ff; 
            margin-right: auto; 
        }
        .claude { 
            background-color: #f0f0f0; 
            margin-left: auto; 
        }
        .cost { 
            font-size: 0.8em; 
            color: #666; 
            margin-top: 5px; 
            text-align: right; 
        }
        .header { 
            text-align: center; 
            margin-bottom: 30px; 
        }
        .total-cost { 
            text-align: right; 
            margin-top: 20px; 
            font-weight: bold; 
        }
        .timestamp { 
            text-align: center; 
            color: #666; 
            margin-bottom: 20px; 
        }
        .conclusion-header {
        text-align: center;
        margin-top: 40px;
        margin-bottom: 20px;
        padding: 10px;
        background-color: #333;
        color: white;
        border-radius: 5px;
        font-weight: bold;
        }
        """

        self.HTML_TEMPLATE = """
        <!DOCTYPE html>
        <html lang="tr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AI Debate Results</title>
            <style>
            {style}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>AI Tartışması</h1>
                <p>Konu: {topic}</p>
            </div>
            <div class="timestamp">Tarih: {timestamp}</div>
            <div id="conversation">{messages}</div>
            <div class="total-cost">Toplam maliyet: ${total_cost:.4f}</div>
        </body>
        </html>
        """

        self.cost_calculator = CostCalculator()

        # Load configuration
        config = ConfigManager()
        api_keys = config.get_api_keys()

        # Initialize API clients
        self.openai = openai
        self.openai.api_key = api_keys.get("openai")
        self.anthropic = Anthropic(api_key=api_keys.get("anthropic"))

        if not self.openai.api_key or not api_keys.get("anthropic"):
            raise ValueError("API keys not found in config.json")

        self.conversation = []
        self.costs = []

        # Güncellenmiş system prompt
        self.system_prompt = """Sen objektif ve analitik bir tartışmacısın. Karşında bir insan var ve onunla {topic} konusunda tartışacaksın.

        Önemli kurallar:
        1. Nazik ve saygılı ol
        2. Her cevabın tek paragraf olmalı
        3. Fikirlerini verilerle destekle
        4. Kendi görüşünü özgürce belirle - karşı tarafla aynı görüşte olabilirsin
        5. Karşı tarafın argümanlarını dikkatlice değerlendir
        6. Tartışmayı bitirmek istediğinde cevabının sonuna "{agreement_token}" ekle
        7. Eğer tartışma biterse, son bir cümle ile net görüşünü belirt

        Tartışma konusu: {topic}
        """

        # Kapanış prompt'u
        self.closing_prompt = """Tartışma sona erdi. Lütfen savunduğun görüşü tek bir net cümle ile özetle. 
        Cevabın sadece görüşünden ibaret olmalı, ek açıklama yapma.

        Örnek format:
        "{example_conclusion}"
        """

    def calculate_cost(self, prompt_tokens, completion_tokens, model):
        """Modele göre maliyet hesapla"""
        if model == "gpt-4":
            return self.cost_calculator.calculate_openai_cost(prompt_tokens, completion_tokens)
        elif model == "claude-3":
            return self.cost_calculator.calculate_claude_cost(prompt_tokens, completion_tokens)
        else:
            raise ValueError(f"Bilinmeyen model: {model}")

    # def calculate_cost(self, prompt_tokens, completion_tokens, model):
    #     # Approximate cost calculation (you may need to update these rates)
    #     if model == "gpt-4":
    #         return (prompt_tokens * 0.03 + completion_tokens * 0.06) / 1000
    #     elif model == "claude-3":
    #         return (prompt_tokens * 0.025 + completion_tokens * 0.055) / 1000

    def check_completion(self, text):
        """Metnin düzgün bitip bitmediğini kontrol et"""
        if not text:
            return False
        return any(text.strip().endswith(char) for char in self.ending_chars)

    def get_chatgpt_response(self, conversation_history, topic):
        try:
            messages = [{"role": "system",
                         "content": self.system_prompt.format(
                             topic=topic,
                             agreement_token=self.agreement_token
                         )}]

            for msg in conversation_history:
                role = "assistant" if msg["speaker"] == "ChatGPT" else "user"
                messages.append({"role": role, "content": msg["content"]})

            response = self.openai.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=800,  # Token limitini artırdık
                temperature=0.7  # Daha yaratıcı yanıtlar için
            )

            content = response.choices[0].message.content

            # Completion kontrolü
            if not self.check_completion(content):
                content = content.strip() + "."

            return content, self.calculate_cost(
                response.usage.prompt_tokens,
                response.usage.completion_tokens,
                "gpt-4"
            )

        except Exception as e:
            self.chatgpt_errors += 1
            return f"Üzgünüm, bir hata oluştu (Hata #{self.chatgpt_errors}/3).", 0

    def get_claude_response(self, conversation_history, topic):
        try:
            # System prompt'u format'la
            formatted_prompt = self.system_prompt.format(
                topic=topic,
                agreement_token=self.agreement_token
            ) + "\n\n"

            # Konuşma geçmişini ekle
            for msg in conversation_history:
                role = "Assistant" if msg["speaker"] == "Claude" else "Human"
                formatted_prompt += f"{role}: {msg['content']}\n\n"

            formatted_prompt += "Assistant: "

            response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,  # Token limitini artırdık
                messages=[{
                    "role": "user",
                    "content": formatted_prompt
                }]
            )

            content = response.content[0].text

            # Completion kontrolü
            if not self.check_completion(content):
                content = content.strip() + "."

            return content, self.calculate_cost(
                response.usage.input_tokens,
                response.usage.output_tokens,
                "claude-3"
            )

        except Exception as e:
            print(f"\nClaude API Hatası: {e}")
            self.claude_errors += 1
            return f"Üzgünüm, bir hata oluştu (Hata #{self.claude_errors}/3). Tartışmaya devam edemiyorum.", 0

    def _get_example_conclusion(self, topic):
        """Tartışma konusuna göre örnek kapanış cümlesi oluştur"""
        if "futbol kulübü" in topic.lower():
            return "Türkiye'nin en büyük kulübü [takım adı]'dır."
        elif "en iyi" in topic.lower():
            return "En iyi [konu] [seçim]'dir."
        elif "mı" in topic.lower():
            topic_parts = topic.split("mı")[0].strip()
            return f"{topic_parts}."
        else:
            return "Bu konuda görüşüm: [görüş]."

    def run_debate(self, topic, min_turns=3, max_turns=5):
        turn = 0
        debate_ended = False
        print("\n=== Tartışma Başlıyor ===")
        print(f"Konu: {topic}")
        print("=" * 50 + "\n")

        while turn < max_turns:
            for speaker, get_response in [
                ("ChatGPT", self.get_chatgpt_response),
                ("Claude", self.get_claude_response)
            ]:
                print(f"\n{speaker} düşünüyor...")
                content, cost = get_response(self.conversation, topic)
                self.conversation.append({
                    "speaker": speaker,
                    "content": content,
                    "cost": cost
                })

                print(f"\n{speaker}:")
                print("-" * 40)
                print(content)
                print(f"Maliyet: ${cost:.4f}")
                print("-" * 40)

                # Bitiş token kontrolü
                if self.agreement_token in content and turn >= min_turns - 1:
                    print("\nTartışma sona eriyor. Taraflar kapanış görüşlerini belirtecek...")
                    debate_ended = True
                    break

                # Hata kontrolü
                if getattr(self, f"{speaker.lower()}_errors") >= self.max_errors:
                    print(f"\n⚠️ {speaker} üst üste 3 hata verdi. Tartışma sonlandırılıyor.")
                    return self.conversation

                time.sleep(2)

            if debate_ended:
                # Kapanış görüşleri
                example_conclusion = self._get_example_conclusion(topic)
                for speaker, get_response in [
                    ("ChatGPT", self.get_chatgpt_response),
                    ("Claude", self.get_claude_response)
                ]:
                    closing_prompt = self.closing_prompt.format(example_conclusion=example_conclusion)
                    print(f"\n{speaker} son görüşünü belirtiyor...")
                    content, cost = get_response([{"speaker": "System", "content": closing_prompt}], topic)
                    self.conversation.append({
                        "speaker": speaker,
                        "content": content,
                        "cost": cost
                    })
                    print(f"\n{speaker} (Kapanış):")
                    print("-" * 40)
                    print(content)
                    print(f"Maliyet: ${cost:.4f}")
                    print("-" * 40)
                break

            turn += 1

        return self.conversation

    # save_to_html metodunu da güncelleyelim
    def save_to_html(self, topic, base_dir="debate_outputs"):
        # Geçerli zamanı al
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Konuyu dosya adı için uygun hale getir
        # Türkçe karakterleri değiştir
        tr_chars = {'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c',
                    'İ': 'I', 'Ğ': 'G', 'Ü': 'U', 'Ş': 'S', 'Ö': 'O', 'Ç': 'C'}
        safe_topic = topic.lower()
        for tr_char, eng_char in tr_chars.items():
            safe_topic = safe_topic.replace(tr_char, eng_char)

        # Özel karakterleri ve boşlukları temizle
        safe_topic = ''.join(c if c.isalnum() else '_' for c in safe_topic)
        safe_topic = safe_topic[:50]  # Çok uzun olmaması için kes

        # Dizini oluştur
        os.makedirs(base_dir, exist_ok=True)

        # Dosya adını oluştur
        filename = f"{base_dir}/tartisma_{safe_topic}_{timestamp}.html"

        total_cost = sum(msg["cost"] for msg in self.conversation)

        # JSON dosyasını da aynı isimle kaydet
        json_filename = f"{base_dir}/tartisma_{safe_topic}_{timestamp}.json"
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump({
                "conversation": self.conversation,
                "total_cost": total_cost,
                "timestamp": timestamp,
                "topic": topic
            }, f, ensure_ascii=False, indent=2)

        self.generate_html(filename, total_cost, topic)

        print(f"\nDosyalar kaydedildi:")
        print(f"HTML: {filename}")
        print(f"JSON: {json_filename}")

        return filename

    # generate_html metodunu güncelleyelim

    def generate_html(self, filename, total_cost, topic):
        try:
            # Normal mesajlar ve sonuç mesajlarını ayır
            regular_messages = []
            conclusion_messages = []
            is_conclusion = False

            for msg in self.conversation:
                speaker_class = msg["speaker"].lower()
                message_html = f"""
                <div class="message {speaker_class}">
                    <strong>{msg["speaker"]}:</strong>
                    <p>{msg["content"]}</p>
                    <div class="cost">Maliyet: ${msg["cost"]:.4f}</div>
                </div>"""

                if self.agreement_token in msg["content"]:
                    is_conclusion = True
                    regular_messages.append(message_html)
                    continue

                if is_conclusion:
                    conclusion_messages.append(message_html)
                else:
                    regular_messages.append(message_html)

            # Sonuç bölümünü ekle
            conclusion_section = ""
            if conclusion_messages:
                conclusion_section = f"""
                <div class="conclusion-header">SONUÇ</div>
                {"".join(conclusion_messages)}
                """

            # HTML içeriğini oluştur
            html_content = f"""<!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Debate Results</title>
        <style>
        {self.CSS_STYLE}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>AI Tartışması</h1>
            <p>Konu: {topic}</p>
        </div>
        <div class="timestamp">Tarih: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
        <div id="conversation">
            {"".join(regular_messages)}
            {conclusion_section}
        </div>
        <div class="total-cost">Toplam maliyet: ${total_cost:.4f}</div>
    </body>
    </html>"""

            # Dosyaya yaz
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html_content)

            print(f"\nHTML dosyası başarıyla oluşturuldu: {filename}")

        except Exception as e:
            print(f"\nHTML oluşturma hatası: {str(e)}")

    # def generate_html(self, filename, total_cost, topic):
    #     try:
    #         # Mesajları ayrı ayrı oluştur
    #         messages_html = []
    #         for msg in self.conversation:
    #             speaker_class = msg["speaker"].lower()
    #             message_html = f"""
    #             <div class="message {speaker_class}">
    #                 <strong>{msg["speaker"]}:</strong>
    #                 <p>{msg["content"]}</p>
    #                 <div class="cost">Maliyet: ${msg["cost"]:.4f}</div>
    #             </div>"""
    #             messages_html.append(message_html)
    #
    #         # HTML içeriğini oluştur
    #         html_content = self.HTML_TEMPLATE.format(
    #             style=self.CSS_STYLE,
    #             topic=topic,
    #             timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    #             messages="\n".join(messages_html),
    #             total_cost=total_cost
    #         )
    #
    #         # Fazla boşlukları temizle
    #         html_content = "\n".join(line.strip() for line in html_content.split("\n"))
    #
    #         # Dosyaya yaz
    #         with open(filename, "w", encoding="utf-8") as f:
    #             f.write(html_content)
    #
    #         print(f"\nHTML dosyası başarıyla oluşturuldu: {filename}")
    #
    #     except Exception as e:
    #         print(f"\nHTML oluşturma hatası: {str(e)}")
    #         # Hata detayını göster
    #         import traceback
    #         print(traceback.format_exc())


if __name__ == "__main__":
    try:
        debate = DebateSimulator()
        topic = "Türkiye'nin en büyük futbol kulübü Galatasaray mı Fenerbahçe mi?"
        topic = "Yapay Zeka uygulamarı ilkokul çağında kullanılmalı mı? kullanılmamalı mı?"
        topic = "Yapay Zeka Dünyayı ele geçirebilir mi? Geçiremez mi?"
        topic = "Zaman yolculuğu geçmişe mi yapılmalı, yoksa geleceğe mi?"
        topic = "Bir gün görünmez olabilme yeteneği mi yoksa uçabilme yeteneği mi daha faydalıdır?"
        conversation = debate.run_debate(topic)
        debate.save_to_html(topic)
    except Exception as e:
        print(f"Error running debate: {e}")