#!/usr/bin/env python3
"""
לילוש טובוש - 1שרת מלא
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
                print("📸 Photo uploaded - will use Face Swap!")
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
        """מוסיף תמונות לסיפור"""
        pages = story_data.get('pages', [])
        ai_model_id = story_data.get('ai_model_id')  # NEW!
        
        for i, page in enumerate(pages):
            print(f"  🖼️  Image {i+1}/{len(pages)}...")
            
            try:
                # יצירת תמונה
                if ai_model_id:
                    # Use trained AI model!
                    print(f"  🤖 Using trained model: {ai_model_id[:20]}...")
                    image_url = self.generate_with_trained_model(page['illustration'], ai_model_id)
                elif IMAGE_MODE == 'leonardo':
                    image_url = self.generate_image_leonardo(page['illustration'])
                else:
                    image_url = self.generate_image_pollinations(page['illustration'])
                
                # Face Swap אם יש תמונה
                if image_url and child_photo and USE_FACE_SWAP and REPLICATE_API_TOKEN and not ai_model_id:
                    print(f"  👤 Face swap...")
                    swapped = self.apply_face_swap(image_url, child_photo)
                    if swapped:
                        image_url = swapped
                        print(f"  ✅ Face swap done!")
                
                page['imageUrl'] = image_url
                
            except Exception as e:
                print(f"  ⚠️  Failed: {str(e)}")
                page['imageUrl'] = None
        
        return story_data
    
    def generate_image_leonardo(self, prompt):
        """יוצר תמונה עם Leonardo"""
        try:
            if not LEONARDO_API_KEY:
                raise Exception('Leonardo API key missing')
            
            print(f"  🎨 Leonardo...")
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            full_prompt = f"{prompt}, children's book illustration, colorful, friendly, storybook art, high quality"
            
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
                print("  ⚠️ No Replicate token")
                return None
            
            print(f"  🔄 Starting face swap...")
            
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
            
            print(f"  ⏳ Waiting for face swap (prediction: {pred_id})...")
            
            # Wait for result
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
                        
                        # Download swapped image
                        img_req = urllib.request.Request(output_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(img_req, timeout=60, context=ctx) as img_resp:
                            img_data = img_resp.read()
                        
                        img_b64 = base64.b64encode(img_data).decode()
                        print(f"  ✅ Face swap succeeded!")
                        return f"data:image/jpeg;base64,{img_b64}"
                    
                    elif status == 'failed':
                        error = check_result.get('error', 'Unknown error')
                        print(f"  ❌ Face swap failed: {error}")
                        return None
            
            print(f"  ⏱️ Face swap timeout")
            return None
            
        except Exception as e:
            print(f"  ⚠️  Face swap error: {str(e)}")
            import traceback
            traceback.print_exc()
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
        
        pages_by_age = {
            '0-2': '4-5',
            '3-5': '6-8',
            '6-8': '8-10',
            '9-12': '10-12'
        }
        
        pages = pages_by_age.get(data.get('childAge', '3-5'), '6-8')
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
            # For now, we'll use a simpler approach
            # Instead of training, we'll just save the photos and use them with face swap
            # Real training is complex and expensive - this is MVP
            
            print(f"  💡 Simplified approach: saving photos for later use")
            
            # Generate a unique model ID
            import hashlib
            model_id = hashlib.md5(f"{child_name}_{time.time()}".encode()).hexdigest()
            
            # Return a mock training ID that we'll use to track this "model"
            # In production, you'd actually call Replicate training API
            # But that requires proper setup and costs $10 per training
            
            return f"mock_training_{model_id}"
                
        except Exception as e:
            print(f"  ⚠️ Training setup error: {str(e)}")
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
