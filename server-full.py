#!/usr/bin/env python3
"""
לילוש טובוש - שרת מלא
Leonardo + Face Swap + PDF
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import urllib.request
import urllib.error
from io import BytesIO
import base64
import os
import time
import ssl

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
    
    def do_GET(self):
        if self.path.startswith('/api/training-status/'):
            training_id = self.path.split('/')[-1]
            self.handle_training_status(training_id)
        else:
            SimpleHTTPRequestHandler.do_GET(self)
    
    def do_POST(self):
        if self.path == '/api/generate-story':
            self.handle_generate_story()
        elif self.path == '/api/suggest-alternative':
            self.handle_suggest_alternative()
        elif self.path == '/api/generate-pdf':
            self.handle_generate_pdf()
        elif self.path == '/api/train-model':
            self.handle_train_model()
        elif self.path.startswith('/api/training-status/'):
            training_id = self.path.split('/')[-1]
            self.handle_training_status(training_id)
        else:
            self.send_error(404)
    
    def handle_generate_story(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            child_name = request_data.get('childName', 'ילד')
            child_photo = request_data.get('childPhoto')
            ai_model_id = request_data.get('ai_model_id')  # NEW!
            
            print(f"\n📖 Creating story for: {child_name}")
            if child_photo:
                print("📸 Photo uploaded - will use InstantID!")
            if ai_model_id:
                print(f"🤖 Using trained AI model: {ai_model_id[:20]}...")
            
            print("📝 Step 1: Generating story with Claude...")
            story_data = self.create_story_with_claude(request_data)
            
            # Add AI model ID to story data
            if ai_model_id:
                story_data['ai_model_id'] = ai_model_id
            
            if IMAGE_MODE != 'none' and story_data.get('pages'):
                print(f"🎨 Step 2: Generating images ({IMAGE_MODE})...")
                story_data = self.add_images_to_story(story_data, child_photo)
            
            print("✅ Story complete!")
            self.send_json_response({
                'success': True,
                'story': story_data
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
            clean_content = content.replace('```json', '').replace('```', '').strip()
            story_data = json.loads(clean_content)
            return story_data
    
    def add_images_to_story(self, story_data, child_photo=None):
        """מוסיף תמונות לסיפור עם InstantID"""
        pages = story_data.get('pages', [])
        
        print(f"  🎨 Creating {len(pages)} images...")
        if child_photo:
            print(f"  👤 Will use InstantID to add child's face!")
        
        for i, page in enumerate(pages):
            print(f"  🖼️  Image {i+1}/{len(pages)}...")
            
            try:
                # Generate base image with Leonardo
                image_url = self.generate_image_leonardo(page['illustration'])
                
                # Apply InstantID if we have a child photo
                if image_url and child_photo and REPLICATE_API_TOKEN:
                    print(f"  👤 Applying InstantID...")
                    face_swapped = self.apply_instant_id(image_url, child_photo)
                    if face_swapped:
                        image_url = face_swapped
                        print(f"  ✅ Child added to image!")
                    else:
                        print(f"  ⚠️ InstantID failed, using original")
                
                page['imageUrl'] = image_url
                
            except Exception as e:
                print(f"  ⚠️  Failed: {str(e)}")
                page['imageUrl'] = None
        
        return story_data
    
    def apply_instant_id(self, target_image_b64, face_image_b64):
        """מוסיף פנים של ילד לתמונה עם InstantID"""
        try:
            if not REPLICATE_API_TOKEN:
                print("  ⚠️ No Replicate token")
                return None
            
            print(f"  🔄 Starting InstantID...")
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            # InstantID expects data URIs
            if not target_image_b64.startswith('data:'):
                target_image_b64 = f"data:image/jpeg;base64,{target_image_b64}"
            
            if not face_image_b64.startswith('data:'):
                face_image_b64 = f"data:image/jpeg;base64,{face_image_b64}"
            
            instant_id_data = {
                "input": {
                    "image": target_image_b64,
                    "face_image": face_image_b64,
                    "prompt": "high quality children's book illustration, colorful, friendly, detailed face",
                    "negative_prompt": "ugly, distorted, low quality, blurry, bad anatomy, scary",
                    "num_steps": 20,
                    "guidance_scale": 5.0,
                    "ip_adapter_scale": 0.8,
                    "seed": 42
                }
            }
            
            headers = {
                'Authorization': f'Token {REPLICATE_API_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            # Use the correct InstantID model
            req = urllib.request.Request(
                'https://api.replicate.com/v1/models/zsxkib/instant-id/predictions',
                data=json.dumps(instant_id_data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30, context=ctx) as response:
                result = json.loads(response.read().decode('utf-8'))
                pred_id = result['id']
            
            print(f"  ⏳ Waiting for InstantID (prediction: {pred_id})...")
            
            # Wait for completion
            for attempt in range(60):
                time.sleep(2)
                
                check_req = urllib.request.Request(
                    f'https://api.replicate.com/v1/predictions/{pred_id}',
                    headers=headers
                )
                
                with urllib.request.urlopen(check_req, timeout=30, context=ctx) as check_resp:
                    check_result = json.loads(check_resp.read().decode('utf-8'))
                    
                    status = check_result['status']
                    
                    if status == 'succeeded':
                        output_url = check_result['output']
                        
                        # Download result
                        if isinstance(output_url, list) and len(output_url) > 0:
                            output_url = output_url[0]
                        
                        img_req = urllib.request.Request(output_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(img_req, timeout=60, context=ctx) as img_resp:
                            img_data = img_resp.read()
                        
                        img_b64 = base64.b64encode(img_data).decode()
                        print(f"  ✅ InstantID succeeded!")
                        return f"data:image/jpeg;base64,{img_b64}"
                    
                    elif status == 'failed':
                        error = check_result.get('error', 'Unknown error')
                        print(f"  ❌ InstantID failed: {error}")
                        return None
            
            print(f"  ⏱️ InstantID timeout")
            return None
            
        except Exception as e:
            print(f"  ⚠️ InstantID error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_image_leonardo(self, prompt, character_reference=None):
        """יוצר תמונה עם Leonardo"""
        try:
            if not LEONARDO_API_KEY:
                raise Exception('Leonardo API key missing')
            
            if character_reference:
                print(f"  🎨 Leonardo (with character reference)...")
            else:
                print(f"  🎨 Leonardo...")
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            # Enhanced prompt for consistency
            full_prompt = f"{prompt}, children's book illustration, simple clean style, soft pastel colors, consistent character design, same character throughout, gentle friendly face, minimalist background, high quality, storybook art"
            
            gen_data = {
                "prompt": full_prompt,
                "modelId": "6bef9f1b-29cb-40c7-b9df-32b51c1f67d3",
                "width": 1024,
                "height": 1024,
                "num_images": 1,
                "seed": 123456789
            }
            
            headers = {
                'Authorization': f'Bearer {LEONARDO_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            req = urllib.request.Request(
                'https://cloud.leonardo.ai/api/rest/v1/generations',
                data=json.dumps(gen_data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30, context=ctx) as response:
                result = json.loads(response.read().decode('utf-8'))
                gen_id = result['sdGenerationJob']['generationId']
            
            # Wait for completion
            for _ in range(60):
                time.sleep(1)
                
                check_req = urllib.request.Request(
                    f'https://cloud.leonardo.ai/api/rest/v1/generations/{gen_id}',
                    headers=headers
                )
                
                with urllib.request.urlopen(check_req, timeout=30, context=ctx) as check_resp:
                    check_result = json.loads(check_resp.read().decode('utf-8'))
                    
                    if check_result['generations_by_pk']['status'] == 'COMPLETE':
                        img_url = check_result['generations_by_pk']['generated_images'][0]['url']
                        
                        # Download
                        img_req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(img_req, timeout=60, context=ctx) as img_resp:
                            img_data = img_resp.read()
                        
                        img_b64 = base64.b64encode(img_data).decode()
                        print(f"  ✅ Done ({len(img_data)} bytes)")
                        
                        return f"data:image/jpeg;base64,{img_b64}"
            
            raise Exception("Timeout")
            
        except Exception as e:
            print(f"  ⚠️  Leonardo error: {str(e)}")
            return None
    
    def generate_image_pollinations(self, prompt):
        """יוצר תמונה עם Pollinations"""
        try:
            import urllib.parse
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            full_prompt = f"{prompt}, children's book illustration, colorful"
            encoded = urllib.parse.quote(full_prompt)
            url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true"
            
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            
            with urllib.request.urlopen(req, timeout=90, context=ctx) as response:
                img_data = response.read()
            
            img_b64 = base64.b64encode(img_data).decode()
            return f"data:image/jpeg;base64,{img_b64}"
            
        except Exception as e:
            print(f"  ⚠️  Pollinations error: {str(e)}")
            return None
    
    def generate_with_trained_model(self, prompt, model_id):
        """יוצר תמונה עם המודל המאומן!"""
        try:
            if not REPLICATE_API_TOKEN:
                raise Exception('Replicate API token missing')
            
            print(f"  🤖 Using trained model...")
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            # Enhanced prompt for children's books
            full_prompt = f"{prompt}, children's book illustration style, colorful, friendly, warm and inviting, storybook art, high quality"
            
            prediction_data = {
                "version": model_id,
                "input": {
                    "prompt": full_prompt,
                    "num_outputs": 1,
                    "aspect_ratio": "1:1",
                    "output_format": "jpg",
                    "output_quality": 90
                }
            }
            
            headers = {
                'Authorization': f'Token {REPLICATE_API_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            req = urllib.request.Request(
                'https://api.replicate.com/v1/predictions',
                data=json.dumps(prediction_data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30, context=ctx) as response:
                result = json.loads(response.read().decode('utf-8'))
                prediction_id = result['id']
            
            # Wait for completion
            for _ in range(60):
                time.sleep(2)
                
                check_req = urllib.request.Request(
                    f'https://api.replicate.com/v1/predictions/{prediction_id}',
                    headers=headers
                )
                
                with urllib.request.urlopen(check_req, timeout=30, context=ctx) as check_resp:
                    check_result = json.loads(check_resp.read().decode('utf-8'))
                    
                    if check_result['status'] == 'succeeded':
                        output_url = check_result['output'][0] if isinstance(check_result['output'], list) else check_result['output']
                        
                        # Download image
                        img_req = urllib.request.Request(output_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(img_req, timeout=60, context=ctx) as img_resp:
                            img_data = img_resp.read()
                        
                        img_b64 = base64.b64encode(img_data).decode()
                        print(f"  ✅ Image with trained model received!")
                        
                        return f"data:image/jpeg;base64,{img_b64}"
                    
                    elif check_result['status'] == 'failed':
                        raise Exception(f"Prediction failed: {check_result.get('error')}")
            
            raise Exception("Timeout waiting for trained model")
            
        except Exception as e:
            print(f"  ⚠️ Trained model error: {str(e)}")
            # Fallback to regular generation
            print(f"  ⚠️ Falling back to Leonardo...")
            return self.generate_image_leonardo(prompt)
    
    def apply_face_swap(self, target_image_b64, source_face_b64):
        """החלפת פנים עם Replicate"""
        try:
            if not REPLICATE_API_TOKEN:
                return None
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            swap_data = {
                "version": "278a81e7ebb22db98bcba54de985d22cc1abeead2754eb1f2af717247be69b34",
                "input": {
                    "target_image": target_image_b64,
                    "swap_image": source_face_b64
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
                pred_id = result['id']
            
            # Wait for result
            for _ in range(60):
                time.sleep(1)
                
                check_req = urllib.request.Request(
                    f'https://api.replicate.com/v1/predictions/{pred_id}',
                    headers=headers
                )
                
                with urllib.request.urlopen(check_req, timeout=30, context=ctx) as check_resp:
                    check_result = json.loads(check_resp.read().decode('utf-8'))
                    
                    if check_result['status'] == 'succeeded':
                        output_url = check_result['output']
                        
                        # Download
                        img_req = urllib.request.Request(output_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(img_req, timeout=60, context=ctx) as img_resp:
                            img_data = img_resp.read()
                        
                        img_b64 = base64.b64encode(img_data).decode()
                        return f"data:image/jpeg;base64,{img_b64}"
                    
                    elif check_result['status'] == 'failed':
                        return None
            
            return None
            
        except Exception as e:
            print(f"  ⚠️  Face swap error: {str(e)}")
            return None
    
    def build_story_prompt(self, data):
        """בונה prompt ל-Claude"""
        theme_names = {
            'animals': 'חיות וטבע',
            'family': 'משפחה ואהבה',
            'space': 'חלל וכוכבים',
            'magic': 'קסם ופנטזיה'
        }
        
        style_names = {
            'funny': 'מצחיק',
            'educational': 'חינוכי'
        }
        
        # For testing: 1 page only!
        pages_by_age = {
            '0-2': '1',
            '3-5': '1',
            '6-8': '1',
            '9-12': '1'
        }
        
        pages = pages_by_age.get(data.get('childAge', '3-5'), '1')
        theme = theme_names.get(data.get('theme', ''), 'הרפתקאות')
        style = style_names.get(data.get('style', ''), 'מצחיק')
        
        prompt = f"""צור סיפור ילדים בעברית:

שם: {data.get('childName', 'ילד')}
גיל: {data.get('childAge', '3-5')}
מגדר: {'בת' if data.get('childGender') == 'girl' else 'בן'}
נושא: {theme}
סגנון: {style}
אורך: {pages} עמודים
"""
        
        if data.get('customInput'):
            prompt += f"פרטים: {data['customInput']}\n"
        
        prompt += """
חשוב: תאר דמויות באופן עקבי!
- אותו כלב בכל העמודים: "small brown fluffy dog"
- אותה חתולה: "white cat with blue eyes"

JSON:
{
  "pages": [
    {"text": "...", "illustration": "A 4 year old child..."}
  ]
}
"""
        return prompt
    
    def handle_suggest_alternative(self):
        """מציע חלופות לטקסט"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            prompt = f"""הצע 3 חלופות:
"{data['currentText']}"

פורמט:
1. ...
2. ...
3. ...
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
            self.send_json_response({'error': str(e)}, status=500)
    
    def handle_generate_pdf(self):
        """יוצר PDF"""
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
            
            print(f"📄 PDF for: {child_name}")
            
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            
            hebrew_font = 'Helvetica'
            font_paths = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                'C:\\Windows\\Fonts\\arial.ttf'
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
            self.send_header('Content-Disposition', f'attachment; filename="lilush_{child_name}.pdf"')
            self.send_header('Content-Length', len(pdf_data))
            self.end_headers()
            self.wfile.write(pdf_data)
            
            print(f"✅ PDF done ({len(pdf_data)} bytes)")
            
        except Exception as e:
            print(f"❌ PDF error: {str(e)}")
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
    
    # ==========================================
    # 🤖 AI Training Endpoints (NEW!)
    # ==========================================
    
    def handle_train_model(self):
        """מאמן מודל AI על בסיס תמונות הילד"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            photos = data.get('photos', [])
            child_name = data.get('child_name', 'child')
            
            print(f"\n🤖 Starting AI Training")
            print(f"📸 Photos: {len(photos)}")
            print(f"👤 Name: {child_name}")
            
            if not REPLICATE_API_TOKEN:
                raise Exception('Replicate API token not configured')
            
            if len(photos) < 5:
                raise Exception('Need at least 5 photos for training')
            
            # Start training
            training_id = self.start_replicate_training(photos, child_name)
            
            if training_id:
                print(f"✅ Training started: {training_id}")
                
                self.send_json_response({
                    'success': True,
                    'training_id': training_id,
                    'message': 'Training started successfully',
                    'estimated_time': '5-10 minutes'
                })
            else:
                raise Exception('Failed to start training')
                
        except Exception as e:
            print(f"❌ Training error: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_json_response({'error': str(e)}, status=500)
    
    def start_replicate_training(self, photos, child_name):
        """מתחיל אימון ב-Replicate - גרסה פשוטה"""
        try:
            if not REPLICATE_API_TOKEN:
                raise Exception('No Replicate token')
            
            print(f"  🚀 REAL Replicate Training starting...")
            print(f"  📸 Photos: {len(photos)}")
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            # Create ZIP from photos
            zip_b64 = self.create_zip_from_photos(photos)
            if not zip_b64:
                raise Exception('Failed to create ZIP')
            
            # Simplified Training - try without specific version first
            print(f"  🔍 Checking available training options...")
            
            # Try simple prediction first to test
            training_data = {
                "input": {
                    "input_images": f"data:application/zip;base64,{zip_b64}",
                    "steps": 500,
                    "trigger_word": child_name
                }
            }
            
            headers = {
                'Authorization': f'Token {REPLICATE_API_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            # Try the trainings endpoint
            training_url = 'https://api.replicate.com/v1/models/ostris/flux-dev-lora-trainer/versions/4a78013f38e8c316fb9bdb7b8b7f81c0059fc7e127e60f03c90fd639b3e6408c/trainings'
            
            req = urllib.request.Request(
                'https://api.replicate.com/v1/trainings',
                data=json.dumps(training_data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            print(f"  📤 Sending training request to Replicate...")
            
            with urllib.request.urlopen(req, timeout=60, context=ctx) as response:
                result = json.loads(response.read().decode('utf-8'))
                training_id = result['id']
            
            print(f"  ✅ Training started: {training_id}")
            print(f"  ⏱️  This will take ~10 minutes...")
            
            return training_id
                
        except Exception as e:
            print(f"  ❌ Training error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def create_zip_from_photos(self, photos):
        """יוצר ZIP מתמונות base64"""
        try:
            import zipfile
            from io import BytesIO
            
            zip_buffer = BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for i, photo_b64 in enumerate(photos):
                    # Remove data:image/... prefix
                    if ',' in photo_b64:
                        photo_b64 = photo_b64.split(',')[1]
                    
                    photo_data = base64.b64decode(photo_b64)
                    zip_file.writestr(f'photo_{i+1}.jpg', photo_data)
            
            zip_data = zip_buffer.getvalue()
            return base64.b64encode(zip_data).decode()
            
        except Exception as e:
            print(f"  ⚠️ ZIP creation error: {str(e)}")
            return None
    
    def handle_training_status(self, training_id):
        """בודק סטטוס של training"""
        try:
            # Mock implementation for MVP
            # In production, this would check real Replicate API
            
            if training_id.startswith('mock_training_'):
                # Simulate training completion after a short delay
                # In real implementation, this would poll Replicate
                
                # Extract model ID from training ID
                model_id = training_id.replace('mock_training_', '')
                
                # For demo purposes, mark as succeeded immediately
                response_data = {
                    'status': 'succeeded',
                    'id': training_id,
                    'model_id': model_id
                }
                
                print(f"✅ Mock training completed: {model_id}")
                
                self.send_json_response(response_data)
                return
            
            # If it's a real Replicate training ID, check it properly
            if not REPLICATE_API_TOKEN:
                raise Exception('Replicate API token not configured')
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            headers = {
                'Authorization': f'Token {REPLICATE_API_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            req = urllib.request.Request(
                f'https://api.replicate.com/v1/trainings/{training_id}',
                headers=headers
            )
            
            with urllib.request.urlopen(req, timeout=30, context=ctx) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                status = result.get('status')
                
                response_data = {
                    'status': status,
                    'id': training_id
                }
                
                if status == 'succeeded':
                    model_version = result.get('output', {}).get('version')
                    if model_version:
                        response_data['model_id'] = model_version
                        print(f"✅ Training completed: {model_version}")
                
                elif status == 'failed':
                    error = result.get('error', 'Unknown error')
                    response_data['error'] = error
                    print(f"❌ Training failed: {error}")
                
                self.send_json_response(response_data)
                
        except Exception as e:
            print(f"❌ Status check error: {str(e)}")
            self.send_json_response({'error': str(e)}, status=500)


def run_server(port=None):
    if port is None:
        port = int(os.environ.get('PORT', 8000))
    
    print("\n" + "="*60)
    print("🚀 לילוש טובוש")
    print("="*60)
    print(f"📸 Images: {IMAGE_MODE}")
    print(f"👤 Face Swap: {'ON' if USE_FACE_SWAP else 'OFF'}")
    print(f"📡 Port: {port}")
    print("="*60 + "\n")
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, CORSRequestHandler)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Stopped!")


if __name__ == '__main__':
    run_server()
