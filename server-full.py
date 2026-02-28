#!/usr/bin/env python3
"""
לילוש טובוש - שרת מלא עם Leonardo + Face Swap
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
LEONARDO_API_KEY = os.environ.get('LEONARDO_API_KEY', '')
REPLICATE_API_TOKEN = os.environ.get('REPLICATE_API_TOKEN', '')
IMAGE_MODE = os.environ.get('IMAGE_MODE', 'leonardo')
USE_FACE_SWAP = os.environ.get('USE_FACE_SWAP', 'true').lower() == 'true'
# ========================================

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

class CORSRequestHandler(SimpleHTTPRequestHandler):
    
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
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            child_name = request_data.get('childName', 'ילד')
            child_photo = request_data.get('childPhoto')  # Base64 photo
            
            print(f"\n📖 Creating story for: {child_name}")
            if child_photo:
                print("📸 With face photo - will use Face Swap!")
            
            if CLAUDE_API_KEY == 'YOUR_CLAUDE_KEY_HERE':
                raise Exception('Claude API key not configured')
            
            print("📝 Step 1: Generating story with Claude...")
            story_data = self.create_story_with_claude(request_data)
            
            if IMAGE_MODE != 'none' and story_data.get('pages'):
                print(f"🎨 Step 2: Generating images ({IMAGE_MODE})...")
                story_data = self.add_images_to_story(story_data, child_photo)
            else:
                print("⏭️  Step 2: Skipping images (mode: none)")
            
            print("✅ Story complete!")
            self.send_json_response({
                'success': True,
                'story': story_data,
                'imageMode': IMAGE_MODE,
                'usedFaceSwap': bool(child_photo and USE_FACE_SWAP)
            })
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_json_response({'error': str(e)}, status=500)
    
    def create_story_with_claude(self, data):
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
            
            clean_content = content.replace('```json', '').replace('```', '').strip()
            story_data = json.loads(clean_content)
            
            return story_data
    
    def add_images_to_story(self, story_data, child_photo=None):
        pages = story_data.get('pages', [])
        
        for i, page in enumerate(pages):
            print(f"  🖼️  Generating image {i+1}/{len(pages)}...")
            
            try:
                # Generate base image
                if IMAGE_MODE == 'leonardo':
                    image_url = self.generate_image_leonardo(page['illustration'])
                else:
                    image_url = self.generate_image_pollinations(page['illustration'])
                
                # Apply face swap if photo provided
                if image_url and child_photo and USE_FACE_SWAP and REPLICATE_API_TOKEN:
                    print(f"  👤 Applying face swap...")
                    swapped_image = self.apply_face_swap(image_url, child_photo)
                    if swapped_image:
                        image_url = swapped_image
                        print(f"  ✅ Face swap successful!")
                    else:
                        print(f"  ⚠️  Face swap failed, using original")
                
                page['imageUrl'] = image_url
                
            except Exception as e:
                print(f"  ⚠️  Failed: {str(e)}")
                page['imageUrl'] = None
        
        return story_data
    
    def apply_face_swap(self, target_image_base64, source_face_base64):
        """החלפת פנים עם Replicate InsightFace"""
        try:
            import ssl
            
            if not REPLICATE_API_TOKEN:
                return None
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            # Replicate Face Swap API
            swap_data = {
                "version": "278a81e7ebb22db98bcba54de985d22cc1abeead2754eb1f2af717247be69b34",
                "input": {
                    "target_image": target_image_base64,
                    "swap_image": source_face_base64
                }
            }
            
            headers = {
                'Authorization': f'Token {REPLICATE_API_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            req = urllib.request.Request(
                'https://api.replicate.com/v1/predictions',
                data=json.dumps(swap_data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30, context=ctx) as response:
                result = json.loads(response.read().decode('utf-8'))
                prediction_id = result['id']
            
            # Poll for result
            for attempt in range(60):
                time.sleep(1)
                
                check_req = urllib.request.Request(
                    f'https://api.replicate.com/v1/predictions/{prediction_id}',
                    headers=headers
                )
                
                with urllib.request.urlopen(check_req, timeout=30, context=ctx) as check_response:
                    check_result = json.loads(check_response.read().decode('utf-8'))
                    
                    if check_result['status'] == 'succeeded':
                        output_url = check_result['output']
                        
                        # Download swapped image
                        img_req = urllib.request.Request(output_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(img_req, timeout=60, context=ctx) as img_response:
                            image_data = img_response.read()
                        
                        # Convert to base64
                        img_str = base64.b64encode(image_data).decode()
                        return f"data:image/jpeg;base64,{img_str}"
                    
                    elif check_result['status'] == 'failed':
                        return None
            
            return None
            
        except Exception as e:
            print(f"  ⚠️ Face swap error: {str(e)}")
            return None
            
        def generate_image_leonardo(self, prompt, character_ref=None):
        """יוצר תמונה עם Leonardo.AI"""
        try:
            import ssl
            
            if not LEONARDO_API_KEY:
                raise Exception('Leonardo API key not configured')
            
            print(f"  🎨 Leonardo: {prompt[:60]}...")
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            enhanced_prompt = f"{prompt}, children's book illustration style, colorful, friendly, warm and inviting, storybook art, high quality, consistent character design"
            
            generation_data = {
                "prompt": enhanced_prompt,
                "modelId": "6bef9f1b-29cb-40c7-b9df-32b51c1f67d3",
                "width": 1024,
                "height": 1024,
                "num_images": 1,
                "guidanceScale": 7,  # ← עקביות
                "seed": 42  # ← אותו seed = תוצאות דומות!
            }
            
            # אם יש character reference (תמונה ראשונה)
            if character_ref:
                generation_data["controlnets"] = [{
                    "initImageId": character_ref,
                    "preprocessorId": 67,  # Character Reference
                    "weight": 0.85
                }]
   
            
            headers = {
                'Authorization': f'Bearer {LEONARDO_API_KEY}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            req = urllib.request.Request(
                'https://cloud.leonardo.ai/api/rest/v1/generations',
                data=json.dumps(generation_data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30, context=ctx) as response:
                result = json.loads(response.read().decode('utf-8'))
                generation_id = result['sdGenerationJob']['generationId']
            
            print(f"  ⏳ Waiting for Leonardo...")
            
            for attempt in range(60):
                time.sleep(1)
                
                check_req = urllib.request.Request(
                    f'https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}',
                    headers=headers
                )
                
                with urllib.request.urlopen(check_req, timeout=30, context=ctx) as check_response:
                    check_result = json.loads(check_response.read().decode('utf-8'))
                    
                    if check_result['generations_by_pk']['status'] == 'COMPLETE':
                        image_url = check_result['generations_by_pk']['generated_images'][0]['url']
                        
                        img_req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(img_req, timeout=60, context=ctx) as img_response:
                            image_data = img_response.read()
                        
                        img_str = base64.b64encode(image_data).decode()
                        
                        print(f"  ✅ Image received ({len(image_data)} bytes)")
                        
                        return f"data:image/jpeg;base64,{img_str}"
            
            raise Exception("Timeout waiting for Leonardo")
            
        except Exception as e:
            print(f"  ⚠️ Leonardo failed: {str(e)}")
            return None
    
    def generate_image_pollinations(self, prompt):
        """יוצר תמונה עם Pollinations.AI"""
        try:
            import urllib.parse
            import ssl
            
            print(f"  🎨 Pollinations: {prompt[:60]}...")
            
            enhanced_prompt = f"{prompt}, children's book illustration, colorful, friendly, warm colors"
            encoded_prompt = urllib.parse.quote(enhanced_prompt)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0'
            })
            
            with urllib.request.urlopen(req, timeout=90, context=ctx) as response:
                image_data = response.read()
            
            img_str = base64.b64encode(image_data).decode()
            
            print(f"  ✅ Image received ({len(image_data)} bytes)")
            
            return f"data:image/jpeg;base64,{img_str}"
            
        except Exception as e:
            print(f"  ⚠️ Pollinations failed: {str(e)}")
            return None
    
    def build_story_prompt(self, data):
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
            '0-2': '4-5',
            '3-5': '6-8',
            '6-8': '8-10',
            '9-12': '10-12'
        }
        
        pages = pages_by_age.get(data.get('childAge', '3-5'), '6-8')
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
      "illustration": "A 4 year old child with a smile, colorful scene"
    }
  ]
}

חשוב: illustration באנגלית לתמונות!
"""
        return prompt
    
    def handle_suggest_alternative(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            prompt = f"""
הצע 3 חלופות למשפט:
"{data['currentText']}"

שם הילד: {data.get('childName', '')}

פורמט:
1. [חלופה 1]
2. [חלופה 2]
3. [חלופה 3]
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
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.lib.utils import simpleSplit
            
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
            
            # Cover
            c.setFont(hebrew_font, 32)
            title = fix_hebrew(f"הספר של {child_name}")
            c.drawString((width - c.stringWidth(title, hebrew_font, 32)) / 2, height - 100, title)
            
            c.showPage()
            
            # Pages
            for i, page in enumerate(pages):
                c.setFont(hebrew_font, 10)
                page_num = fix_hebrew(f"עמוד {i + 1}")
                c.drawString(width - 100, height - 30, page_num)
                
                # Text
                c.setFont(hebrew_font, 14)
                text = fix_hebrew(page.get('text', ''))
                lines = simpleSplit(text, hebrew_font, 14, width - 100)
                
                y_position = height - 280
                for line in lines:
                    line_width = c.stringWidth(line, hebrew_font, 14)
                    c.drawString((width - line_width) / 2, y_position, line)
                    y_position -= 20
                
                c.showPage()
            
            c.save()
            
            pdf_data = buffer.getvalue()
            buffer.close()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/pdf')
            self.send_header('Content-Disposition', f'attachment; filename="lilush_tovush_{child_name}.pdf"')
            self.send_header('Content-Length', len(pdf_data))
            self.end_headers()
            self.wfile.write(pdf_data)
            
            print(f"✅ PDF generated ({len(pdf_data)} bytes)")
            
        except ImportError as e:
            print(f"❌ Missing library: {str(e)}")
            self.send_json_response({'error': 'Missing required library for PDF'}, status=500)
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
    if port is None:
        port = int(os.environ.get('PORT', 8000))
    
    print("\n" + "="*60)
    print("🚀 לילוש טובוש - Server Starting!")
    print("="*60)
    print(f"📸 Image mode: {IMAGE_MODE}")
    print(f"👤 Face Swap: {'Enabled' if USE_FACE_SWAP and REPLICATE_API_TOKEN else 'Disabled'}")
    print("="*60)
    print(f"📡 Server: http://localhost:{port}")
    print("="*60 + "\n")
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, CORSRequestHandler)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped!")


if __name__ == '__main__':
    run_server()
