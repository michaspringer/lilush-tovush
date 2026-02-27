#!/usr/bin/env python3
"""
לילוש טובוש - שרת מלא
תומך ב:
- יצירת סיפורים (Claude)
- יצירת תמונות (Hugging Face / Leonardo)
- PDF בעברית
- הצעת חלופות
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import urllib.request
import urllib.error
from io import BytesIO
import base64
import os
import time

# ========================================
# 🔑 API Keys
# ========================================
CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY', 'YOUR_CLAUDE_KEY_HERE')
HUGGINGFACE_TOKEN = os.environ.get('HUGGINGFACE_TOKEN', 'YOUR_HF_TOKEN_HERE')
LEONARDO_API_KEY = os.environ.get('LEONARDO_API_KEY', '')  # אופציונלי

# מצב תמונות: 'huggingface' או 'leonardo' או 'none'
IMAGE_MODE = os.environ.get('IMAGE_MODE', 'huggingface')
# ========================================

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

class CORSRequestHandler(SimpleHTTPRequestHandler):
    """Handler עם CORS ו-API endpoints"""
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        SimpleHTTPRequestHandler.end_headers(self)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()
    
    def do_POST(self):
        if self.path == '/api/generate-story':
            self.handle_generate_story()
        elif self.path == '/api/suggest-alternative':
            self.handle_suggest_alternative()
        elif self.path == '/api/generate-pdf':
            self.handle_generate_pdf()
        else:
            self.send_error(404)
    
    def handle_generate_story(self):
        """יוצר סיפור + תמונות"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            child_name = request_data.get('childName', 'ילד')
            print(f"\n📖 Creating story for: {child_name}")
            
            # בדיקת מפתחות
            if CLAUDE_API_KEY == 'YOUR_CLAUDE_KEY_HERE':
                raise Exception('Claude API key not configured')
            
            # 1. יצירת הסיפור
            print("📝 Step 1: Generating story with Claude...")
            story_data = self.create_story_with_claude(request_data)
            
            # 2. יצירת תמונות
            if IMAGE_MODE != 'none' and story_data.get('pages'):
                print(f"🎨 Step 2: Generating images ({IMAGE_MODE})...")
                story_data = self.add_images_to_story(story_data)
            else:
                print("⏭️  Step 2: Skipping images (mode: none)")
            
            print("✅ Story complete!")
            self.send_json_response({
                'success': True,
                'story': story_data,
                'imageMode': IMAGE_MODE
            })
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_json_response({'error': str(e)}, status=500)
    
    def create_story_with_claude(self, data):
        """יוצר סיפור עם Claude"""
        prompt = self.build_story_prompt(data)
        
        claude_request = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': CLAUDE_API_KEY,
            'anthropic-version': '2023-06-01'
        }
        
        req = urllib.request.Request(
            CLAUDE_API_URL,
            data=json.dumps(claude_request).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=60) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            content = response_data['content'][0]['text']
            
            # Parse JSON
            clean_content = content.replace('```json', '').replace('```', '').strip()
            story_data = json.loads(clean_content)
            
            return story_data
    
    def add_images_to_story(self, story_data):
        """מוסיף תמונות לסיפור"""
        pages = story_data.get('pages', [])
        
        for i, page in enumerate(pages):
            print(f"  🖼️  Generating image {i+1}/{len(pages)}...")
            
            try:
                if IMAGE_MODE == 'huggingface':
                    image_url = self.generate_image_huggingface(page['illustration'])
                elif IMAGE_MODE == 'leonardo':
                    image_url = self.generate_image_leonardo(page['illustration'])
                else:
                    image_url = None
                
                page['imageUrl'] = image_url
                
            except Exception as e:
                print(f"  ⚠️  Failed: {str(e)}")
                page['imageUrl'] = None
        
        return story_data
    
    def generate_image_huggingface(self, prompt):
        """יוצר תמונה עם Pollinations.AI (חינמי לגמרי!)"""
        try:
            import urllib.request
            import urllib.parse
            import base64
            import ssl
            
            print(f"  🎨 Pollinations: {prompt[:60]}...")
            
            # Pollinations - API חינמי לחלוטין ללא הגבלה!
            enhanced_prompt = f"{prompt}, children's book illustration, colorful, friendly, warm colors, high quality"
            encoded_prompt = urllib.parse.quote(enhanced_prompt)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&enhance=true"
            
            # SSL context
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            # Download image
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            with urllib.request.urlopen(req, timeout=90, context=ctx) as response:
                image_data = response.read()
            
            # Convert to base64
            img_str = base64.b64encode(image_data).decode()
            
            print(f"  ✅ Image received ({len(image_data)} bytes)")
            
            return f"data:image/jpeg;base64,{img_str}"
            
        except Exception as e:
            print(f"  ⚠️ Pollinations failed: {str(e)}")
            return None
                
                return f"data:image/jpeg;base64,{img_str}"
            
        except Exception as e:
            print(f"  ⚠️  DeepAI failed: {str(e)}")
            # אם גם זה נכשל - פשוט תחזיר None
            return None
    
    def generate_image_leonardo(self, prompt):
        """יוצר תמונה עם Leonardo.AI"""
        # TODO: יישום עתידי
        if not LEONARDO_API_KEY:
            raise Exception('Leonardo API key not configured')
        
        # Leonardo API call here
        # ...
        
        return None
    
    def build_story_prompt(self, data):
        """בונה prompt ליצירת סיפור"""
        theme_names = {
            'animals': 'חיות וטבע',
            'family': 'משפחה ואהבה',
            'space': 'חלל וכוכבים',
            'magic': 'קסם ופנטזיה'
        }
        
        style_names = {
            'funny': 'מצחיק ומשעשע',
            'educational': 'חינוכי ומלמד'
        }
        
        pages_by_age = {
            '0-2': '8-10',
            '3-5': '12-14',
            '6-8': '16-18',
            '9-12': '20-24'
        }
        
        pages = pages_by_age.get(data.get('childAge', '3-5'), '12-14')
        theme = theme_names.get(data.get('theme', ''), 'הרפתקאות')
        style = style_names.get(data.get('style', ''), 'מצחיק')
        
        prompt = f"""
צור סיפור ילדים בעברית:

פרטי הילד:
- שם: {data.get('childName', 'ילד')}
- גיל: {data.get('childAge', '3-5')}
- מגדר: {'בת' if data.get('childGender') == 'girl' else 'בן'}

מאפייני הסיפור:
- נושא: {theme}
- סגנון: {style}
- אורך: {pages} עמודים
"""
        
        if data.get('customInput'):
            prompt += f"- פרטים מיוחדים: {data['customInput']}\n"
        
        prompt += """
דרישות:
1. הילד הוא הגיבור הראשי
2. כל עמוד: 1-2 משפטים
3. צורות פניה נכונות
4. מסר חיובי

פורמט JSON:
{
  "pages": [
    {
      "text": "טקסט העמוד בעברית",
      "illustration": "A 4 year old child with a smile, colorful bedroom, warm atmosphere"
    }
  ]
}

חשוב: illustration צריך להיות באנגלית! זה prompt ליצירת תמונה.
"""
        return prompt
    
    def handle_suggest_alternative(self):
        """מציע חלופות למשפט"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            prompt = f"""
הצע 3 חלופות למשפט זה בספר ילדים:
"{data['currentText']}"

שם הילד: {data.get('childName', '')}

דרישות:
1. 3 חלופות שונות
2. אותו אורך בערך
3. שמור על שם הילד
4. מתאים לספר ילדים

פורמט:
1. [חלופה ראשונה]
2. [חלופה שנייה]
3. [חלופה שלישית]
"""
            
            claude_request = {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': CLAUDE_API_KEY,
                'anthropic-version': '2023-06-01'
            }
            
            req = urllib.request.Request(
                CLAUDE_API_URL,
                data=json.dumps(claude_request).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=60) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                content = response_data['content'][0]['text']
                
                lines = content.strip().split('\n')
                alternatives = []
                for line in lines:
                    clean = line.strip()
                    if clean and len(clean) > 5:
                        if clean[0].isdigit() and '. ' in clean:
                            clean = clean.split('. ', 1)[1]
                        alternatives.append(clean)
                
                self.send_json_response({
                    'success': True,
                    'alternatives': alternatives[:3]
                })
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            self.send_json_response({'error': str(e)}, status=500)
    
    def handle_generate_pdf(self):
        """יוצר PDF"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.lib.utils import simpleSplit
            
            # BiDi
            try:
                from bidi.algorithm import get_display
                import arabic_reshaper
                has_bidi = True
            except:
                has_bidi = False
            
            def fix_hebrew(text):
                if not has_bidi:
                    return text
                try:
                    reshaped = arabic_reshaper.reshape(text)
                    return get_display(reshaped)
                except:
                    return text
            
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            story_data = json.loads(post_data.decode('utf-8'))
            
            child_name = story_data.get('childName', 'ילד')
            pages = story_data.get('pages', [])
            
            print(f"📄 Generating PDF for: {child_name}")
            
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            
            # פונט
            hebrew_font = 'Helvetica'
            font_paths = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                'C:\\Windows\\Fonts\\arial.ttf',
            ]
            
            for font_path in font_paths:
                try:
                    pdfmetrics.registerFont(TTFont('Hebrew', font_path))
                    hebrew_font = 'Hebrew'
                    break
                except:
                    continue
            
            # עמוד שער
            c.setFont(hebrew_font, 32)
            title = fix_hebrew(f"הספר של {child_name}")
            c.drawString((width - c.stringWidth(title, hebrew_font, 32)) / 2, height - 100, title)
            
            c.setFont(hebrew_font, 16)
            subtitle = fix_hebrew("סיפור מותאם אישית")
            c.drawString((width - c.stringWidth(subtitle, hebrew_font, 16)) / 2, height - 150, subtitle)
            
            c.showPage()
            
            # עמודי סיפור
            for i, page in enumerate(pages):
                c.setFont(hebrew_font, 10)
                page_num = fix_hebrew(f"עמוד {i + 1}")
                c.drawString(width - 100, height - 30, page_num)
                
                # placeholder לתמונה (ימין)
                c.setFillColorRGB(0.8, 0.9, 0.9)
                illustration_x = width - 350
                c.rect(illustration_x, height - 250, 300, 180, fill=1)
                c.setFillColorRGB(0, 0, 0)
                
                # טקסט
                c.setFont(hebrew_font, 14)
                text = fix_hebrew(page.get('text', ''))
                lines = simpleSplit(text, hebrew_font, 14, width - 100)
                
                y_position = height - 280
                for line in lines:
                    line_width = c.stringWidth(line, hebrew_font, 14)
                    c.drawString((width - line_width) / 2, y_position, line)
                    y_position -= 20
                
                c.showPage()
            
            # עמוד סיום
            c.setFont(hebrew_font, 28)
            end_text = fix_hebrew("סוף הסיפור")
            c.drawString((width - c.stringWidth(end_text, hebrew_font, 28)) / 2, height / 2, end_text)
            
            c.save()
            
            pdf_data = buffer.getvalue()
            buffer.close()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/pdf')
            self.send_header('Content-Disposition', 'attachment; filename="lilush_tovush_story.pdf"')
            self.send_header('Content-Length', len(pdf_data))
            self.end_headers()
            self.wfile.write(pdf_data)
            
            print(f"✅ PDF generated ({len(pdf_data)} bytes)")
            
        except ImportError as e:
            print(f"❌ Missing library: {str(e)}")
            self.send_json_response({'error': 'Missing required library. Install: pip install reportlab python-bidi arabic-reshaper'}, status=500)
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_json_response({'error': str(e)}, status=500)
    
    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def log_message(self, format, *args):
        if self.path.startswith('/api/'):
            return
        SimpleHTTPRequestHandler.log_message(self, format, *args)


def run_server(port=None):
    # קבלת PORT מהסביבה (Railway/Render) או default 8000
    if port is None:
        port = int(os.environ.get('PORT', 8000))
    # בדיקות
    print("\n" + "="*60)
    print("🚀 לילוש טובוש - Server Starting")
    print("="*60)
    
    if CLAUDE_API_KEY == 'YOUR_CLAUDE_KEY_HERE':
        print("⚠️  Claude API key not set!")
    else:
        print("✅ Claude API key configured")
    
    if IMAGE_MODE == 'huggingface':
        if HUGGINGFACE_TOKEN == 'YOUR_HF_TOKEN_HERE':
            print("⚠️  HuggingFace token not set!")
        else:
            print("✅ HuggingFace token configured")
            try:
                import huggingface_hub
                print("✅ huggingface_hub installed")
            except:
                print("❌ huggingface_hub NOT installed")
                print("   Run: pip install huggingface_hub Pillow")
    
    if IMAGE_MODE == 'leonardo':
        if LEONARDO_API_KEY:
            print("✅ Leonardo API key configured")
        else:
            print("⚠️  Leonardo API key not set")
    
    print(f"\n📸 Image mode: {IMAGE_MODE}")
    print("="*60)
    print(f"📡 Server: http://localhost:{port}")
    print(f"🌐 Open: http://localhost:{port}/index.html")
    print("="*60)
    print("💡 Press Ctrl+C to stop")
    print("="*60 + "\n")
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, CORSRequestHandler)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped!")


if __name__ == '__main__':
    run_server()
