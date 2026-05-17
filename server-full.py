#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Children's Book Generator - Full Server
Leonardo + Fal.ai Face Swap + PDF + InstantID + LoRA
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import urllib.request
import urllib.error
from io import BytesIO
import base64
import os
import re
import time
import ssl


def safe_slug(name, fallback_prefix="child"):
    """
    ממיר שם בעברית/לטינית ל-slug בטוח ל-URL ול-Replicate.
    Replicate דורש: רק אותיות לטיניות קטנות, מספרים, ומקפים.
    """
    if not name:
        return f"{fallback_prefix}-{int(time.time())}"
    
    name = name.strip().lower()
    
    # אם השם כבר באנגלית בלבד - נקה ושמור
    if re.match(r'^[a-z0-9\s_-]+$', name):
        slug = re.sub(r'[\s_]+', '-', name)
        slug = re.sub(r'-+', '-', slug).strip('-')
        return slug if slug else f"{fallback_prefix}-{int(time.time())}"
    
    # אם יש תווי עברית/אחרים - השתמש ב-prefix + timestamp
    return f"{fallback_prefix}-{int(time.time())}"

# ========================================
# API Keys
# ========================================
CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY', 'YOUR_CLAUDE_KEY_HERE')
LEONARDO_API_KEY = os.environ.get('LEONARDO_API_KEY', '')
REPLICATE_API_TOKEN = os.environ.get('REPLICATE_API_TOKEN', '')
REPLICATE_USERNAME = os.environ.get('REPLICATE_USERNAME', '')  # Your Replicate username
FAL_KEY = os.environ.get('FAL_KEY', '')
IMAGE_MODE = os.environ.get('IMAGE_MODE', 'leonardo')

# Cloudinary for LoRA training
CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL', '')
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME', '')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY', '')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET', '')

# Parse CLOUDINARY_URL if provided
if CLOUDINARY_URL and not CLOUDINARY_CLOUD_NAME:
    # Format: cloudinary://api_key:api_secret@cloud_name
    import re
    match = re.match(r'cloudinary://([^:]+):([^@]+)@(.+)', CLOUDINARY_URL)
    if match:
        CLOUDINARY_API_KEY = match.group(1)
        CLOUDINARY_API_SECRET = match.group(2)
        CLOUDINARY_CLOUD_NAME = match.group(3)
        print(f"✅ Cloudinary configured from CLOUDINARY_URL: {CLOUDINARY_CLOUD_NAME}")

# Try to import fal_client
try:
    import fal_client
    HAS_FAL = True
except ImportError:
    HAS_FAL = False
    print("⚠️ fal_client not installed - face swap disabled")

# Try to import replicate
try:
    import replicate
    HAS_REPLICATE = True
    if REPLICATE_API_TOKEN:
        os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN
except ImportError:
    HAS_REPLICATE = False
    print("⚠️ replicate not installed - LoRA training disabled")
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
        elif self.path.startswith('/api/lora-status/'):
            training_id = self.path.split('/')[-1]
            self.handle_lora_status(training_id)
        elif self.path == '/' or self.path == '/index-full.html':
            # Serve index-full.html
            self.serve_file('index-full.html', 'text/html')
        elif self.path == '/app-full.js':
            self.serve_file('app-full.js', 'application/javascript')
        elif self.path == '/styles-full.css':
            self.serve_file('styles-full.css', 'text/css')
        else:
            # Try default handler
            try:
                SimpleHTTPRequestHandler.do_GET(self)
            except:
                self.send_error(404)
    
    def serve_file(self, filename, content_type):
        """Serve a static file"""
        try:
            with open(filename, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404)
        except Exception as e:
            print(f"Error serving {filename}: {e}")
            self.send_error(500)
    
    def do_POST(self):
        if self.path == '/api/generate-story':
            self.handle_generate_story()
        elif self.path == '/api/suggest-alternative':
            self.handle_suggest_alternative()
        elif self.path == '/api/generate-pdf':
            self.handle_generate_pdf()
        elif self.path == '/api/train-model':
            self.handle_train_model()
        elif self.path == '/api/regenerate-image':
            self.handle_regenerate_image()
        elif self.path == '/api/test-face-swap':
            self.handle_test_face_swap()
        elif self.path == '/api/start-lora-training':
            self.handle_start_lora_training()
        elif self.path == '/api/preview-lora':  # 🆕 NEW: LoRA preview check
            self.handle_preview_lora()
        elif self.path == '/api/preview-options':  # 🆕 NEW: 3 preview options
            self.handle_preview_options()
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
            ai_model_id = request_data.get('ai_model_id')
            
            # 🎓 NEW: LoRA parameters
            lora_url = request_data.get('lora_url')
            trigger_word = request_data.get('trigger_word')
            lora_version = request_data.get('lora_version')  # 🆕 NEW: trained model version
            use_lora = request_data.get('use_lora', False) and lora_url and trigger_word
            
            # 🎲 NEW: chosen seed - ה-seed שההורה בחר בתצוגה המקדימה
            chosen_seed = request_data.get('chosen_seed')
            
            print(f"\n📖 Creating story for: {child_name}")
            if use_lora:
                print(f"🎓 USING TRAINED LoRA MODEL!")
                print(f"   Trigger word: {trigger_word}")
                print(f"   LoRA URL: {lora_url[:80]}...")
                if lora_version:
                    print(f"   Version: {lora_version[:80]}...")
                if chosen_seed is not None:
                    print(f"   🎲 Chosen seed: {chosen_seed} (consistent for whole book)")
            elif child_photo:
                print("📸 Photo uploaded - will use FLUX face swap")
            if ai_model_id:
                print(f"🤖 Using trained AI model: {ai_model_id[:20]}...")
            
            print("📝 Step 1: Generating story with Claude...")
            story_data = self.create_story_with_claude(request_data)
            
            if ai_model_id:
                story_data['ai_model_id'] = ai_model_id
            
            if IMAGE_MODE != 'none' and story_data.get('pages'):
                print(f"🎨 Step 2: Generating images ({IMAGE_MODE})...")
                # 🎓 העבר את ה-LoRA ואת ה-seed לפונקציה
                story_data = self.add_images_to_story(
                    story_data,
                    child_photo,
                    lora_url=lora_url if use_lora else None,
                    trigger_word=trigger_word if use_lora else None,
                    lora_version=lora_version if use_lora else None,
                    chosen_seed=chosen_seed  # 🎲 עקביות לכל הספר
                )
            
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
    
    def handle_preview_lora(self):
        """
        🆕 יוצר תמונת תצוגה מקדימה אחת של הילד עם ה-LoRA המאומן.
        זה לפני יצירת ספר שלם - כדי שהמשתמש יראה איך הילד נראה.
        """
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            child_name = data.get('child_name', '')
            lora_url = data.get('lora_url')
            trigger_word = data.get('trigger_word')
            lora_version = data.get('lora_version')
            theme = data.get('theme', 'animals')
            
            if not lora_url or not trigger_word:
                raise Exception('LoRA not configured for this child')
            
            print(f"\n🔍 Generating LoRA preview for: {child_name}")
            print(f"   Trigger: {trigger_word}")
            
            # 🛡️ פרומפט בדיקה - תמיד ילד יחיד, ללא אנשים נוספים!
            # חשוב: לא להזכיר "family members" או "friends" - גורם לשכפול דמות
            theme_scenes = {
                'animals': 'in a colorful zoo, friendly cartoon animals in the background, happy smile',
                'family': 'in a cozy warm living room, soft sunlight, happy smile',
                'space': 'floating among stars and colorful planets, amazed happy expression',
                'magic': 'in a magical sparkling forest with glowing lights, wondrous happy look'
            }
            scene = theme_scenes.get(theme, theme_scenes['animals'])
            
            # יצירת תמונה אחת לבדיקה
            # medium shot (לא close-up) - עקבי עם הספר, מונע שכפול וריאליזם
            preview_image = self.generate_image_with_lora(
                prompt=f"medium shot, {scene}",
                lora_url=lora_url,
                trigger_word=trigger_word,
                lora_version=lora_version
            )
            
            if not preview_image:
                raise Exception('Failed to generate preview image')
            
            print(f"   ✅ Preview ready!")
            
            self.send_json_response({
                'success': True,
                'preview_image': preview_image,
                'child_name': child_name,
                'message': f'תצוגה מקדימה של {child_name}'
            })
            
        except Exception as e:
            print(f"❌ Preview error: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def handle_preview_options(self):
        """
        🆕 יוצר 3 תמונות תצוגה מקדימה במקביל - כל אחת עם seed שונה.
        ההורה יבחר את הטובה ביותר, וה-seed שלה יישמר לכל הספר (עקביות!).
        """
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            child_name = data.get('child_name', '')
            lora_url = data.get('lora_url')
            trigger_word = data.get('trigger_word')
            lora_version = data.get('lora_version')
            theme = data.get('theme', 'animals')
            
            if not lora_url or not trigger_word:
                raise Exception('LoRA not configured for this child')
            
            print(f"\n🎨 Generating 3 preview options for: {child_name}")
            print(f"   Trigger: {trigger_word}")
            
            # 🛡️ סצנת בדיקה - תמיד ילד יחיד, ללא אנשים נוספים
            theme_scenes = {
                'animals': 'in a colorful zoo, friendly cartoon animals in the background, happy smile',
                'family': 'in a cozy warm living room, soft sunlight, happy smile',
                'space': 'floating among stars and colorful planets, amazed happy expression',
                'magic': 'in a magical sparkling forest with glowing lights, wondrous happy look'
            }
            scene = theme_scenes.get(theme, theme_scenes['animals'])
            
            # 🎲 3 seeds קבועים ושונים - כל אחד ייתן תמונה אחרת
            import random
            seeds = [random.randint(1, 999999) for _ in range(3)]
            print(f"   🎲 Seeds: {seeds}")
            
            # 🚀 יצירת 3 התמונות במקביל (threads)
            import threading
            results = [None, None, None]
            
            def generate_one(index, seed):
                try:
                    print(f"   🖼️  Option {index+1}/3 (seed={seed})...")
                    img = self.generate_image_with_lora(
                        prompt=f"medium shot, {scene}",
                        lora_url=lora_url,
                        trigger_word=trigger_word,
                        lora_version=lora_version,
                        seed=seed
                    )
                    results[index] = {'image': img, 'seed': seed}
                except Exception as e:
                    print(f"   ⚠️ Option {index+1} failed: {e}")
                    results[index] = None
            
            threads = []
            for i, seed in enumerate(seeds):
                t = threading.Thread(target=generate_one, args=(i, seed))
                threads.append(t)
                t.start()
            
            # המתנה לסיום כל ה-threads
            for t in threads:
                t.join()
            
            # סינון תוצאות שהצליחו
            options = [r for r in results if r and r.get('image')]
            
            if not options:
                raise Exception('Failed to generate any preview options')
            
            print(f"   ✅ {len(options)}/3 preview options ready!")
            
            self.send_json_response({
                'success': True,
                'options': options,  # [{image, seed}, ...]
                'child_name': child_name
            })
            
        except Exception as e:
            print(f"❌ Preview options error: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
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
    
    def add_images_to_story(self, story_data, child_photo=None, lora_url=None, trigger_word=None, lora_version=None, chosen_seed=None):
        """מוסיף תמונות לסיפור - עם LoRA אם יש, אחרת FLUX + face swap.
        
        chosen_seed: אם ניתן - כל עמודי הספר ישתמשו ב-seed הזה (עקביות מלאה!).
        """
        pages = story_data.get('pages', [])
        
        use_lora = lora_url and trigger_word
        
        # 📖 NEW: Character Bible - מילון דמויות שClaude יצר
        characters = story_data.get('characters', [])
        char_dict = {}  # name -> english_description
        for char in characters:
            name = char.get('name', '').strip()
            desc = char.get('english_description', '').strip()
            if name and desc:
                char_dict[name] = desc
        
        if char_dict:
            print(f"  📖 Character Bible: {len(char_dict)} characters")
            for name, desc in char_dict.items():
                print(f"     - {name}: {desc[:60]}...")
        
        # 🎽 בחירת ביגוד אחיד לכל הספר
        consistent_outfit = None
        if use_lora:
            import random
            outfits = [
                "wearing a yellow t-shirt and blue jeans",
                "wearing a red striped shirt and khaki shorts",
                "wearing a green hoodie and dark blue pants",
                "wearing a white t-shirt with a pattern and beige pants",
                "wearing an orange sweater and denim shorts",
                "wearing a purple shirt and gray pants",
                "wearing a blue polo shirt and brown shorts",
            ]
            consistent_outfit = random.choice(outfits)
            print(f"  🎽 Outfit chosen for entire book: {consistent_outfit}")
            story_data['outfit'] = consistent_outfit
        
        # שמירת ה-Character Bible כך שיהיה זמין לrenegerate
        story_data['character_bible'] = char_dict
        
        if use_lora:
            print(f"  🎓 Creating {len(pages)} images with LoRA model!")
            print(f"  🏷️  Trigger word: {trigger_word}")
            if lora_version:
                print(f"  📌 Using trained model version directly")
        elif child_photo:
            print(f"  🎨 Creating {len(pages)} images with FLUX + face swap...")
            print(f"  👤 Child will be drawn in illustration style!")
        else:
            print(f"  🎨 Creating {len(pages)} images with FLUX (no child)...")
        
        for i, page in enumerate(pages):
            print(f"\n  🖼️  Image {i+1}/{len(pages)}...")
            
            # 🐌 Throttle - חכה בין בקשות LoRA
            # 🎯 NEW: גם לפני הראשון! כי Claude קרא ל-API קודם וצורך 1 בקשה
            if use_lora:
                wait_seconds = 12 if i > 0 else 8  # Wait less before first since Claude was earlier
                print(f"  ⏱️  Waiting {wait_seconds}s (rate limit protection)...")
                time.sleep(wait_seconds)
            
            try:
                if use_lora:
                    # 🎓 מסלול LoRA עם Character Bible
                    illustration = page.get('illustration', '')
                    page_text = page.get('text', '')  # הטקסט העברי של העמוד
                    chars_in_scene = page.get('characters_in_scene', [])
                    
                    # 🛡️ FIX: זיהוי אוטומטי של דמויות בעמוד
                    # לא סומכים רק על characters_in_scene של Claude!
                    # סורקים את הטקסט והתיאור - אם שם דמות מופיע, מוסיפים אותה
                    detected_chars = set(chars_in_scene)
                    for char_name in char_dict.keys():
                        # בדיקה אם שם הדמות מופיע בטקסט העברי או בתיאור
                        if char_name in page_text or char_name in illustration:
                            if char_name not in detected_chars:
                                detected_chars.add(char_name)
                                print(f"  🔍 Auto-detected character '{char_name}' in page text")
                    
                    # 🎯 בנה description עם Character Bible
                    char_descriptions = []
                    for char_name in detected_chars:
                        if char_name in char_dict:
                            char_descriptions.append(char_dict[char_name])
                    
                    if char_descriptions:
                        print(f"  📖 Using {len(char_descriptions)} character description(s) from Bible")
                    
                    image_url = self.generate_image_with_lora(
                        prompt=illustration,
                        lora_url=lora_url,
                        trigger_word=trigger_word,
                        lora_version=lora_version,
                        outfit=consistent_outfit,
                        character_descriptions=char_descriptions,  # 🆕
                        seed=chosen_seed  # 🎲 אותו seed לכל הספר - עקביות!
                    )
                    
                    # Fallback אם נכשל
                    if not image_url:
                        print(f"  ⚠️  LoRA failed after retries, falling back to FLUX...")
                        image_url = self.generate_image_flux_with_face(
                            illustration,
                            child_photo
                        )
                else:
                    # מסלול רגיל - FLUX + face swap
                    image_url = self.generate_image_flux_with_face(
                        page['illustration'],
                        child_photo
                    )
                
                page['imageUrl'] = image_url
                
            except Exception as e:
                print(f"  ⚠️  Failed: {str(e)}")
                page['imageUrl'] = None
        
        return story_data
    
    def apply_fal_face_swap(self, target_image_b64, face_image_b64):
        """Face swap with Fal.ai - simple and working"""
        try:
            if not FAL_KEY or not HAS_FAL:
                print("  ⚠️ Fal.ai not configured")
                return None
            
            print(f"  🎭 Starting Fal.ai face swap...")
            
            # Set API key
            os.environ["FAL_KEY"] = FAL_KEY
            
            # Use simple face-swap
            handler = fal_client.submit(
                "fal-ai/face-swap",
                arguments={
                    "base_image_url": target_image_b64,
                    "swap_image_url": face_image_b64
                }
            )
            
            print(f"  ⏳ Waiting for Fal.ai...")
            
            result = handler.get()
            
            if result and 'image' in result:
                output_url = result['image']['url']
                
                # Download result
                req = urllib.request.Request(
                    output_url,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                with urllib.request.urlopen(req, timeout=60, context=ctx) as response:
                    img_data = response.read()
                
                img_b64 = base64.b64encode(img_data).decode()
                print(f"  ✅ Fal.ai face swap succeeded!")
                return f"data:image/jpeg;base64,{img_b64}"
            
            print(f"  ⚠️ Fal.ai: No output")
            return None
            
        except Exception as e:
            print(f"  ⚠️ Fal.ai error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def apply_instant_id(self, target_image_b64, face_image_b64):
        """Face swap with working Replicate model"""
        try:
            if not REPLICATE_API_TOKEN:
                print("  ⚠️ No Replicate token")
                return None
            
            print(f"  🎭 Starting Face Swap...")
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            # Ensure data URIs
            if not target_image_b64.startswith('data:'):
                target_image_b64 = f"data:image/jpeg;base64,{target_image_b64}"
            
            if not face_image_b64.startswith('data:'):
                face_image_b64 = f"data:image/jpeg;base64,{face_image_b64}"
            
            # Use simpler face swap - just swap the prediction endpoint
            swap_data = {
                "input": {
                    "target_image": target_image_b64,
                    "swap_image": face_image_b64
                }
            }
            
            headers = {
                'Authorization': f'Token {REPLICATE_API_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            # Try lucataco/faceswap - more reliable
            req = urllib.request.Request(
                'https://api.replicate.com/v1/models/lucataco/faceswap/predictions',
                data=json.dumps(swap_data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30, context=ctx) as response:
                result = json.loads(response.read().decode('utf-8'))
                pred_id = result['id']
            
            print(f"  ⏳ Face swap processing... ({pred_id})")
            
            # Poll for result
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
                        
                        # Download
                        img_req = urllib.request.Request(output_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(img_req, timeout=60, context=ctx) as img_resp:
                            img_data = img_resp.read()
                        
                        img_b64 = base64.b64encode(img_data).decode()
                        print(f"  ✅ Face swap succeeded!")
                        return f"data:image/jpeg;base64,{img_b64}"
                    
                    elif status == 'failed':
                        error = check_result.get('error', 'Unknown')
                        print(f"  ❌ Face swap failed: {error}")
                        return None
            
            print(f"  ⏱️ Face swap timeout")
            return None
            
        except Exception as e:
            print(f"  ⚠️ Face swap error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
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
    
    def translate_to_english(self, hebrew_text):
        """תרגום תיאור תמונה מעברית לאנגלית - מודע להקשר של ספרי ילדים"""
        try:
            if not CLAUDE_API_KEY:
                return hebrew_text  # Fallback
            
            prompt = f"""You are translating a scene description for a children's book illustration from Hebrew to English.

Hebrew description: "{hebrew_text}"

CRITICAL translation rules:
1. This is a CHILDREN'S BOOK scene - translate concretely and literally
2. Watch for animal body parts - translate them EXACTLY:
   - "חדק" = "trunk" (elephant's trunk) - NEVER "snake"!
   - "זנב" = "tail"
   - "כנף" = "wing"
   - "טלף" = "hoof"
   - "קרן" = "horn"
3. If an animal is mentioned, ALWAYS name the animal explicitly in English
4. Translate every object and creature mentioned - don't drop anything
5. Be vivid and specific so an illustrator can draw it accurately

Return ONLY the English translation, no explanations."""
            
            claude_request = {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 300,
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
            
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                english_text = response_data['content'][0]['text'].strip()
                print(f"  🌐 Translated: {english_text[:60]}...")
                return english_text
                
        except Exception as e:
            print(f"  ⚠️ Translation failed: {str(e)}, using original")
            return hebrew_text
    
    def _story_to_image_description(self, hebrew_story_text, character_bible=None):
        """
        🎯 ממיר טקסט סיפור בעברית לתיאור תמונה באנגלית.
        
        זה שונה מ-translate_to_english:
        - translate_to_english: תרגום ישר של תיאור תמונה
        - _story_to_image_description: מתחקר טקסט סיפור ומחזיר תיאור ויזואלי בלבד
        
        character_bible: מילון {שם: תיאור אנגלי} - עוזר לזהות דמויות בעלות שם.
        
        דוגמה:
        טקסט: "ציפור צהובה התקרבה לדולב והגישה לו פרח אדום"
        חוזר: "yellow bird offering red flower, garden, sunny day"
        """
        try:
            if not CLAUDE_API_KEY:
                return hebrew_story_text
            
            # 🔑 בניית הקשר דמויות - אם יש Character Bible
            character_context = ""
            if character_bible:
                lines = []
                for name, desc in character_bible.items():
                    lines.append(f'- "{name}" is: {desc}')
                if lines:
                    character_context = (
                        "\n\nKNOWN CHARACTERS (use these descriptions if the name appears):\n"
                        + "\n".join(lines)
                        + "\n(If the text mentions a character name, use its full description above!)"
                    )
            
            prompt = f"""Convert this Hebrew children's story sentence into an English image description (15-25 words).

CRITICAL RULES:
1. Describe what should be VISUALLY in the image (scene, action, objects, creatures)
2. DO NOT describe the child's appearance (hair, eyes, age, clothes) - we have a special model
3. DO NOT mention the child's name
4. INCLUDE every animal, object, and creature mentioned in the text - don't drop anything!

⚠️ ANIMAL BODY PARTS - translate EXACTLY:
- "חדק" = "trunk" (elephant trunk) - NEVER translate as "snake"!
- "זנב" = "tail",  "כנף" = "wing",  "טלף" = "hoof",  "קרן" = "horn"
- When an animal is mentioned, NAME the animal explicitly (elephant, dog, bird...){character_context}

Hebrew text: "{hebrew_story_text}"

Examples of good descriptions:
- "yellow bird offering red flower, garden, sunny day"
- "large grey elephant wrapping its trunk gently around child, jungle background"
- "small brown puppy jumping near child on green grass, afternoon light"
- "reaching up toward the moon, starry night sky"

Return ONLY the English description, nothing else."""
            
            claude_request = {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 100,
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
            
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                description = response_data['content'][0]['text'].strip()
                print(f"  🎨 Image description: {description}")
                return description
                
        except Exception as e:
            print(f"  ⚠️ Story-to-image conversion failed: {str(e)}, falling back to translation")
            return self.translate_to_english(hebrew_story_text)
    
    def generate_image_flux_with_face(self, prompt, child_photo=None):
        """יצירת תמונה עם FLUX + InstantID - הילד מצוייר באיור!"""
        try:
            if not FAL_KEY or not HAS_FAL:
                raise Exception('Fal.ai not configured')
            
            print(f"  🎨 FLUX + InstantID...")
            
            # Translate Hebrew to English if needed
            if any(ord(c) > 127 for c in prompt):
                prompt = self.translate_to_english(prompt)
            
            # FLUX prompt - emphasize illustration style
            full_prompt = f"{prompt}, children's book illustration style, colorful, friendly, warm, high quality, professional illustration"
            
            negative_prompt = "realistic photo, photographic, multiple people, crowd, side view, back view, profile view, hidden face, blurry, low quality"
            
            print(f"  📝 Prompt: {full_prompt[:80]}...")
            
            # Set API key
            os.environ["FAL_KEY"] = FAL_KEY
            
            # Note: InstantID requires specific Replicate model access
            # For now, using FLUX + Face Swap as reliable fallback
            # TODO: Get proper InstantID model access from Replicate
            
            # Fallback: FLUX + Face Swap
            handler = fal_client.submit(
                "fal-ai/flux/dev",
                arguments={
                    "prompt": full_prompt,
                    "image_size": "landscape_4_3",
                    "num_inference_steps": 28,
                    "guidance_scale": 3.5,
                    "num_images": 1,
                    "enable_safety_checker": False,
                    "negative_prompt": negative_prompt
                }
            )
            
            print(f"  ⏳ Waiting for FLUX...")
            
            result = handler.get()
            
            if result and 'images' in result and len(result['images']) > 0:
                output_url = result['images'][0]['url']
                
                # Download
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                req = urllib.request.Request(
                    output_url,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                
                with urllib.request.urlopen(req, timeout=60, context=ctx) as response:
                    img_data = response.read()
                
                img_b64 = base64.b64encode(img_data).decode()
                image_data = f"data:image/jpeg;base64,{img_b64}"
                
                print(f"  ✅ FLUX done! ({len(img_data)} bytes)")
                
                # Apply face swap if child photo provided
                if child_photo:
                    print(f"  👤 Applying face swap...")
                    face_swapped = self.apply_fal_face_swap(image_data, child_photo)
                    if face_swapped:
                        print(f"  ✅ Child's face added to image!")
                        return face_swapped
                    else:
                        print(f"  ⚠️ Face swap failed, using original FLUX image")
                
                return image_data
            
            raise Exception("No output from FLUX")
            
        except Exception as e:
            print(f"  ⚠️ Image generation error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
            
            # Fallback: Regular FLUX without face reference
            handler = fal_client.submit(
                "fal-ai/flux/dev",
                arguments={
                    "prompt": full_prompt,
                    "image_size": "landscape_4_3",
                    "num_inference_steps": 28,
                    "guidance_scale": 3.5,
                    "num_images": 1,
                    "enable_safety_checker": False
                }
            )
            
            print(f"  ⏳ Waiting for FLUX...")
            
            result = handler.get()
            
            if result and 'images' in result and len(result['images']) > 0:
                output_url = result['images'][0]['url']
                
                # Download
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                req = urllib.request.Request(
                    output_url,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                
                with urllib.request.urlopen(req, timeout=60, context=ctx) as response:
                    img_data = response.read()
                
                img_b64 = base64.b64encode(img_data).decode()
                print(f"  ✅ FLUX done! ({len(img_data)} bytes)")
                return f"data:image/jpeg;base64,{img_b64}"
            
            raise Exception("No output from FLUX")
            
        except Exception as e:
            print(f"  ⚠️ FLUX error: {str(e)}")
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
            
            # Translate Hebrew to English if needed
            if any(ord(c) > 127 for c in prompt):  # Contains non-ASCII (Hebrew)
                prompt = self.translate_to_english(prompt)
            
            # Balanced prompt - clear facial features for face swap while maintaining illustration style
            full_prompt = f"{prompt}, illustrated children's book style, character with clear visible face and distinct facial features, expressive friendly eyes, recognizable human-like face, colorful vibrant illustration, warm and inviting, professional children's book art, digital illustration"
            
            negative_prompt = "no face, hidden face, side view, back view, abstract, overly simplified, stick figure, blurry, distorted, scary, dark, photorealistic, realistic photo"
            
            gen_data = {
                "prompt": full_prompt,
                "negative_prompt": negative_prompt,
                "modelId": "6bef9f1b-29cb-40c7-b9df-32b51c1f67d3",
                "width": 1024,
                "height": 1024,
                "num_images": 1,
                "seed": 123456789,
                "num_inference_steps": 30,  # ← Balanced detail
                "guidance_scale": 7.5,  # ← Balanced adherence
                "presetStyle": "ILLUSTRATION"
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
        
        # Full book - 6 pages!
        pages_by_age = {
            '0-2': '4',
            '3-5': '6',
            '6-8': '8',
            '9-12': '10'
        }
        
        pages = pages_by_age.get(data.get('childAge', '3-5'), '1')
        theme = theme_names.get(data.get('theme', ''), 'הרפתקאות')
        style = style_names.get(data.get('style', ''), 'מצחיק')
        
        # 🎯 NEW: בדיקה אם משתמשים ב-LoRA - אם כן, נשנה את הוראות התמונות
        use_lora = bool(data.get('use_lora') and data.get('trigger_word'))
        
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
        
        # 🎯 שתי גרסאות שונות של הוראות תיאור התמונה - תלוי אם יש LoRA
        if use_lora:
            # 🎓 גרסה ל-LoRA: Character Bible + הוראות מחמירות לדמות יחידה
            prompt += """
חשוב מאוד! הוראות לכתיבת הסיפור:

📖 שלב ראשון - Character Bible (מילון דמויות):
לפני העמודים, צור מילון של כל הדמויות (מלבד הילד הראשי).
לכל דמות נוספת (חבר, חיה, יצור) - תן תיאור באנגלית קבוע ומפורט שיופיע בכל הספר.

⚠️ התיאור חייב להיות מאוד ספציפי - לעקביות לאורך הספר:
- גזע מדויק (golden retriever puppy / black labrador / tabby cat)
- צבע מדויק (golden-brown fur / black and white)
- גודל (small / medium / large)
- מאפיינים ייחודיים (floppy ears, fluffy tail, blue collar)
דוגמה טובה: "a small golden retriever puppy, fluffy golden-brown fur, 
floppy ears, dark eyes, red collar"
דוגמה רעה: "a dog" (כללי מדי - ייצא שונה בכל עמוד!)

🚫 כללים קריטיים:
1. אל תתאר את הילד הראשי בכלל - יש לו מודל מאומן!
2. דמויות אחרות חייבות להיות בעלות תיאור באנגלית מפורט וספציפי
3. לכל סצנה - בחר אם הילד לבד או עם דמות אחת אחרת (לא יותר!)
4. חיות לא לובשות בגדים! אל תזכיר ביגוד עבור חיות.

🔑 כלל זהב - דמויות בעלות שם:
אם דמות יש לה שם (למשל "פיצי הפיל", "פליק הכלב") - בכל עמוד שהיא מופיעה,
ה-illustration חייב לכלול את **סוג** הדמות, לא רק את השם!

❌ טעות נפוצה:
   עמוד 1: text="פיצי הפיל שיחק" / illustration="elephant playing"  ✓
   עמוד 5: text="פיצי חיבק את דולב" / illustration="pitzi hugging child"  ✗
   (בעמוד 5 ה-AI לא יודע ש"פיצי" = פיל! יצייר משהו אקראי!)

✅ נכון:
   עמוד 5: text="פיצי חיבק את דולב" / illustration="the elephant hugging 
   the child with its trunk, jungle"
   (תמיד "elephant", גם אם הטקסט אומר רק "פיצי")

📌 חוק: ב-illustration תמיד תכתוב את הסוג (elephant/dog/lion),
   אף פעם לא רק את השם הפרטי (פיצי/פליק).

⭐ הכלל הכי חשוב - סנכרון טקסט-תמונה:
כל יצור, חיה, אובייקט או אלמנט שמוזכר ב-text (העברית)
חייב להופיע גם ב-illustration (האנגלית)!

דוגמה:
❌ טעות: text="הפיל חיבק את דולב בחדק" / illustration="hugging in jungle"
   (אין פיל בתיאור! התמונה תצא בלי פיל!)
✅ נכון: text="הפיל חיבק את דולב בחדק" / illustration="a large grey elephant 
   wrapping its trunk around the child, jungle background"

לפני שאתה כותב illustration - עבור על ה-text ושאל:
"אילו דברים מוזכרים? פיל? עץ? כדור? כולם חייבים להיות ב-illustration!"

⚠️ זהירות עם איברי גוף של חיות - תרגם נכון לאנגלית:
- חדק של פיל = "elephant trunk" (לא snake! לא נחש!)
- זנב = "tail",  כנף = "wing",  טלף = "hoof",  קרן = "horn"
- תמיד תכתוב את שם החיה במפורש: "elephant", "dog", "lion"
דוגמה: "הפיל הרים את דולב בחדק" → "an elephant lifting the child with its trunk"
(שים לב: trunk, ולא snake!)

📝 מבנה הסיפור:
- text (עברית): טקסט מתאים לגיל
- illustration (אנגלית): description שכולל את כל האלמנטים מהטקסט (15-25 words)

⚠️ כללים לתיאור תמונה:
✓ אם רק הילד בסצנה: "alone, [scene with all objects], medium shot"
✓ אם יש דמות/חיה: "with [full description], [scene with all objects]"
✗ אל תתאר את הילד: "boy with brown hair", "wearing blue" - אסור!
✗ אל תכתוב "another child" / "second kid" - גורם לשכפול פנים!
✗ אל תשכח אף יצור/אובייקט שמוזכר בטקסט!

📏 סוג צילום - השתמש ב-"medium shot" ברוב העמודים:
- "medium shot" - הילד נראה מהמותניים ומעלה (מומלץ ברירת מחדל)
- "wide shot" - סצנה מלאה (טוב לעמודי פתיחה/סיום)
- הימנע מ-"close-up" קיצוני - זה גורם לסגנון לא עקבי בין עמודים

✅ דוגמאות טובות:
   "alone, joyful in colorful zoo with lions and giraffes, medium shot, sunny day"
   "with a large grey elephant lifting the child with its trunk, jungle, wide shot"
   "alone, holding a red balloon, reaching toward a yellow butterfly, green park, medium shot"

❌ דוגמאות רעות:
   "with another child" → גורם לכפילות פנים!
   "playing happily" → איפה הפיל/הכלב שמוזכר בטקסט?!
   "A boy wearing green" → תיאור מיותר ואסור של הילד

פורמט JSON מדויק:
{
  "characters": [
    {
      "name": "פליק",
      "english_description": "small brown dog with floppy ears, fluffy fur, friendly eyes",
      "type": "dog"
    }
  ],
  "pages": [
    {
      "text": "הטקסט בעברית...",
      "illustration": "alone, playing in colorful zoo with lions, joyful, close-up shot",
      "characters_in_scene": []
    },
    {
      "text": "דולב פגש את פליק הכלב ליד עץ גדול...",
      "illustration": "with the dog flick beside a big oak tree, green garden, sunny afternoon",
      "characters_in_scene": ["פליק"]
    }
  ]
}

חשוב: אם characters ריק - הילד לבד בכל הסיפור (פשוט יותר ובטוח יותר).
זכור: כל מה שבטקסט - חייב להיות גם בתיאור התמונה!
"""
        else:
            # גרסה רגילה: תיאור מפורט (לFLUX רגיל)
            prompt += """
חשוב מאוד!
1. הטקסט (text) בעברית בלבד!
2. תיאור התמונה (illustration) גם בעברית!
3. תאר דמויות באופן עקבי בכל העמודים
4. דוגמה: "ילד בן 4 עם שיער קצר וחום לובש חולצה כחולה..."

פורמט JSON:
{
  "pages": [
    {
      "text": "הטקסט בעברית כאן...",
      "illustration": "ילד בן 4 עם שיער קצר חום עומד בגן חיות צבעוני..."
    }
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
    
    def handle_regenerate_image(self):
        """מייצר תמונה מחדש עם הנחיות מהמשתמש - תומך ב-LoRA"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            page_text = data.get('page_text', '')
            user_prompt = data.get('user_prompt', '').strip()
            child_photo = data.get('child_photo')
            
            # 🎓 LoRA parameters
            lora_url = data.get('lora_url')
            trigger_word = data.get('trigger_word')
            lora_version = data.get('lora_version')
            outfit = data.get('outfit')
            character_descriptions = data.get('character_descriptions', [])  # 🆕
            character_bible = data.get('character_bible', {})  # 🆕 מילון מלא
            use_lora = bool(lora_url and trigger_word)
            
            print(f"\n🎨 Regenerating image...")
            if use_lora:
                print(f"  🎓 Using LoRA: {trigger_word}")
            if character_descriptions:
                print(f"  📖 Characters in scene: {len(character_descriptions)}")
            if user_prompt:
                print(f"  👤 User request: {user_prompt[:50]}...")
            print(f"  📖 Page text: {page_text[:80]}...")
            
            # 🎯 NEW: אם הטקסט בעברית - בקש מ-Claude להפוך אותו לתיאור תמונה
            # מעבירים גם את ה-Character Bible כדי שידע ש"פיצי" = פיל
            if any(ord(c) > 127 for c in page_text):
                print(f"  🔄 Converting Hebrew story text to image description...")
                image_description = self._story_to_image_description(page_text, character_bible)
                print(f"  📝 Image description: {image_description[:80]}...")
            else:
                image_description = page_text
            
            # Combine user prompt with image description
            if user_prompt:
                final_prompt = f"{user_prompt}, {image_description}"
            else:
                final_prompt = image_description
            
            print(f"  📝 Final prompt: {final_prompt[:100]}...")
            
            # 🎓 STRATEGY 1: Use LoRA if available (preferred!)
            if use_lora:
                image_url = self.generate_image_with_lora(
                    prompt=final_prompt,
                    lora_url=lora_url,
                    trigger_word=trigger_word,
                    lora_version=lora_version,
                    outfit=outfit,
                    character_descriptions=character_descriptions  # 🆕
                )
                
                if not image_url:
                    print(f"  ⚠️  LoRA failed, falling back to FLUX...")
                    image_url = self.generate_image_flux_with_face(final_prompt, child_photo)
            else:
                # STRATEGY 2: Fallback to FLUX + face swap
                image_url = self.generate_image_flux_with_face(final_prompt, child_photo)
            
            if not image_url:
                raise Exception("Failed to generate image")
            
            # Apply face swap only if NOT using LoRA (LoRA already includes the child)
            if not use_lora and child_photo and FAL_KEY and HAS_FAL:
                print(f"  👤 Applying Fal.ai face swap...")
                face_swapped = self.apply_fal_face_swap(image_url, child_photo)
                if face_swapped:
                    image_url = face_swapped
                    print(f"  ✅ Child added to image!")
                else:
                    print(f"  ⚠️ Face swap failed, using original image")
            
            print(f"  ✅ Image regenerated successfully!")
            
            self.send_json_response({
                'success': True,
                'imageUrl': image_url
            })
            
        except Exception as e:
            error_msg = str(e)
            print(f"  ❌ Regeneration error: {error_msg}")
            import traceback
            traceback.print_exc()
            self.send_json_response({
                'success': False,
                'error': error_msg
            }, status=500)
    
    def handle_test_face_swap(self):
        """בודק face swap עם תמונת בדיקה - מהיר!"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            child_photo = data.get('child_photo')
            child_name = data.get('child_name', 'ילד')
            
            if not child_photo:
                raise Exception('No child photo provided')
            
            print(f"\n🧪 Testing face swap for {child_name}...")
            
            # Test prompt - simple scene
            test_prompt = f"A cheerful child in a colorful playground, playing happily, sunny day"
            
            print(f"  📝 Test prompt: {test_prompt}")
            
            # Generate test image with FLUX
            image_url = self.generate_image_flux_with_face(test_prompt, child_photo)
            
            if not image_url:
                raise Exception("Failed to generate test image")
            
            print(f"  ✅ Test complete!")
            
            self.send_json_response({
                'success': True,
                'imageUrl': image_url,
                'message': 'Test image generated successfully!'
            })
            
        except Exception as e:
            error_msg = str(e)
            print(f"  ❌ Test error: {error_msg}")
            import traceback
            traceback.print_exc()
            self.send_json_response({
                'success': False,
                'error': error_msg
            }, status=500)
    
    def handle_start_lora_training(self):
        """מתחיל אימון LoRA עם Cloudinary + Replicate - גרסה מתוקנת"""
        try:
            if not HAS_REPLICATE or not REPLICATE_API_TOKEN:
                raise Exception('Replicate not configured')
            
            if not CLOUDINARY_CLOUD_NAME or not CLOUDINARY_API_KEY:
                raise Exception('Cloudinary not configured')
            
            if not REPLICATE_USERNAME:
                raise Exception('REPLICATE_USERNAME not configured in environment variables')
            
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            child_photos = data.get('child_photos', [])
            child_name_raw = data.get('child_name', '').strip()
            
            if not child_name_raw:
                raise Exception('Child name required')
            
            if len(child_photos) < 5:
                raise Exception(f'Need at least 5 photos, got {len(child_photos)}')
            
            # 🔧 FIX 1: שם בטוח ל-URL (פותר בעיית עברית בURL)
            child_slug = safe_slug(child_name_raw)
            
            print(f"\n🎓 Starting LoRA training")
            print(f"  👤 Child name (display): {child_name_raw}")
            print(f"  🔗 Child slug (API): {child_slug}")
            print(f"  📸 Photos: {len(child_photos)}")
            
            # Configure Cloudinary
            import cloudinary
            import cloudinary.uploader
            
            cloudinary.config(
                cloud_name=CLOUDINARY_CLOUD_NAME,
                api_key=CLOUDINARY_API_KEY,
                api_secret=CLOUDINARY_API_SECRET
            )
            
            # 🔧 FIX 2: trigger_word באנגלית בלבד
            trigger_word = f"{child_slug.replace('-', '_')}_kid"
            print(f"  🏷️  Trigger word: {trigger_word}")
            
            # Create ZIP
            import tempfile
            import zipfile
            
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, 'training_images.zip')
            
            print(f"  💾 Creating ZIP...")
            
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for i, photo_b64 in enumerate(child_photos):
                    if ',' in photo_b64:
                        photo_b64 = photo_b64.split(',')[1]
                    
                    photo_data = base64.b64decode(photo_b64)
                    
                    photo_filename = f"image_{i+1}.jpg"
                    photo_path = os.path.join(temp_dir, photo_filename)
                    
                    with open(photo_path, 'wb') as f:
                        f.write(photo_data)
                    
                    zipf.write(photo_path, photo_filename)
            
            print(f"  📦 ZIP: {os.path.getsize(zip_path)} bytes")
            
            # 🔧 FIX 4: העלאה ל-Cloudinary כקובץ ציבורי
            # type="upload" + access_mode="public" מבטיחים שReplicate יוכל להוריד
            print(f"  ☁️  Uploading to Cloudinary (public)...")
            upload_result = cloudinary.uploader.upload(
                zip_path,
                resource_type="raw",
                type="upload",
                folder="lora_training",
                public_id=f"{child_slug}_{int(time.time())}",
                access_mode="public",
                use_filename=False,
                unique_filename=False
            )
            
            zip_url = upload_result['secure_url']
            print(f"  ✅ Uploaded: {zip_url}")
            
            # 🔧 FIX 5: ודא שה-URL נגיש לפני שולח ל-Replicate
            # אם Cloudinary מחזיר 401, נכשל מהר ובהבנה
            print(f"  🔍 Verifying URL is publicly accessible...")
            try:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                req = urllib.request.Request(
                    zip_url,
                    headers={'User-Agent': 'Mozilla/5.0'},
                    method='HEAD'
                )
                with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                    if resp.status == 200:
                        print(f"  ✅ URL is publicly accessible (HTTP 200)")
                    else:
                        print(f"  ⚠️  URL returned HTTP {resp.status}")
            except urllib.error.HTTPError as he:
                if he.code == 401 or he.code == 403:
                    raise Exception(
                        f'Cloudinary URL not publicly accessible (HTTP {he.code}). '
                        f'Check Cloudinary settings: Settings → Security → '
                        f'"Restricted media types" should NOT include "raw", '
                        f'and "Resource list" delivery should be allowed.'
                    )
                else:
                    print(f"  ⚠️  HEAD check returned {he.code}, continuing anyway...")
            except Exception as verify_error:
                print(f"  ⚠️  Could not verify URL ({verify_error}), continuing anyway...")
            
            # 🔧 FIX 3: יצור את המודל ב-Replicate לפני training
            # זה הפתרון לבעיית 404 "destination does not exist"
            model_name = f"{child_slug}-lora"
            destination = f"{REPLICATE_USERNAME}/{model_name}"
            
            print(f"  📍 Destination: {destination}")
            print(f"  🏗️  Ensuring model exists at Replicate...")
            
            try:
                replicate.models.create(
                    owner=REPLICATE_USERNAME,
                    name=model_name,
                    visibility="private",
                    hardware="gpu-t4",
                    description=f"LoRA model for child book - {child_name_raw}"
                )
                print(f"  ✅ Model created: {destination}")
            except Exception as model_error:
                err_str = str(model_error).lower()
                # אם המודל כבר קיים - זה בסדר, ממשיכים
                if "already exists" in err_str or "already taken" in err_str or "422" in err_str:
                    print(f"  ℹ️  Model already exists: {destination}")
                else:
                    print(f"  ❌ Failed to create model: {model_error}")
                    raise Exception(f'Could not create Replicate model: {model_error}')
            
            # Start Replicate training
            print(f"  🎓 Starting Replicate training...")
            
            training = replicate.trainings.create(
                version="ostris/flux-dev-lora-trainer:e440909d3512c31646ee2e0c7d6f6f4923224863a6a10c494606e79fb5844497",
                input={
                    "input_images": zip_url,
                    "trigger_word": trigger_word,
                    "steps": 1000,
                    "learning_rate": 0.0004,
                    "resolution": "512,768,1024",
                    "autocaption": True
                },
                destination=destination
            )
            
            print(f"  ✅ Training started: {training.id}")
            
            self.send_json_response({
                'success': True,
                'training_id': training.id,
                'trigger_word': trigger_word,
                'destination': destination,
                'child_name': child_name_raw,
                'child_slug': child_slug,
                'estimated_time': 600
            })
            
        except Exception as e:
            error_msg = str(e)
            print(f"  ❌ Training error: {error_msg}")
            import traceback
            traceback.print_exc()
            self.send_json_response({
                'success': False,
                'error': error_msg
            }, status=500)
    
    def handle_lora_status(self, training_id):
        """בודק סטטוס אימון LoRA"""
        try:
            if not HAS_REPLICATE:
                raise Exception('Replicate not configured')
            
            print(f"  🔍 Checking LoRA training: {training_id}")
            
            training = replicate.trainings.get(training_id)
            
            response = {
                'training_id': training_id,
                'status': training.status
            }
            
            if training.status == 'succeeded':
                response['lora_url'] = training.output.get('weights')
                response['version'] = training.output.get('version')
                print(f"  ✅ Training completed!")
            elif training.status == 'failed':
                response['error'] = training.error
                print(f"  ❌ Training failed: {training.error}")
            else:
                print(f"  ⏳ Status: {training.status}")
            
            self.send_json_response(response)
            
        except Exception as e:
            print(f"  ❌ Status error: {str(e)}")
            self.send_json_response({
                'status': 'error',
                'error': str(e)
            }, status=500)
    
    def generate_image_with_lora(self, prompt, lora_url, trigger_word, style_name="illustration", lora_version=None, outfit=None, character_descriptions=None, seed=None):
        """יוצר תמונה עם LoRA מאומן.
        
        אם lora_version קיים - משתמשים במודל המאומן ישירות (האסטרטגיה הטובה יותר!)
        אחרת - נופלים חזרה ל-ostris/flux-dev-lora (legacy)
        
        אם outfit ניתן - הילד ילבש את אותו ביגוד בכל התמונות בספר.
        אם character_descriptions ניתן - מוסיפים תיאור דמויות נלוות (כלב, חבר, וכו').
        """
        try:
            if not HAS_REPLICATE:
                raise Exception('Replicate not configured')
            
            # Style-specific prompts
            style_prompts = {
                "illustration": "children's book illustration style, warm colors, soft lighting, detailed",
                "watercolor": "watercolor painting, soft colors, artistic, gentle",
                "cartoon": "cartoon style, bold colors, playful, fun",
                "realistic": "realistic digital art, detailed, professional",
                "comic": "comic book style, bold lines, vibrant"
            }
            
            style_prompt = style_prompts.get(style_name, style_prompts["illustration"])
            
            # Translate Hebrew to English if needed (still useful for legacy/non-LoRA mode)
            if any(ord(c) > 127 for c in prompt):
                prompt = self.translate_to_english(prompt)
            
            # 🎯 בניית פרומפט אופטימלית עבור LoRA
            outfit_part = f"{outfit}" if outfit else ""
            
            # 📖 הוספת Character Bible descriptions
            char_part = ""
            has_other_chars = False
            if character_descriptions:
                # הפרדה ברורה: כל דמות מתוארת בנפרד
                char_list = ". ".join(character_descriptions)
                char_part = char_list
                has_other_chars = True
            
            # 🧹 ניקוי שוליים - למנוע רגליים/ידיים חתוכות
            clean_composition = (
                "clean composition, well-framed, centered subjects, "
                "full scene visible, no cropped people, no body parts at edges"
            )
            
            # 🎨 עיגון סגנון איור רך - "Sandwich technique" מאוזן
            style_anchor_start = "a warm children's book illustration, soft digital painting style, "
            style_anchor_end = (
                ", consistent storybook illustration, "
                "painterly art style, warm soft colors, gentle lighting"
            )
            
            # 🎯 בניית הפרומפט - מבנה מובנה עם הפרדה ברורה בין דמויות
            if has_other_chars:
                # 🐕 יש דמות נוספת (כלב/חבר) - מבנה מפורש שמפריד ביניהן
                # חשוב: מתארים את הילד כיחידה סגורה, ואז הדמות כיחידה נפרדת
                # כדי שה-outfit לא "ידלוף" לכלב
                child_block = (
                    f"ONE human child as main character "
                    f"({trigger_word}), the child wearing {outfit_part}, "
                    f"detailed facial features, recognizable face"
                    if outfit_part else
                    f"ONE human child as main character "
                    f"({trigger_word}), detailed facial features, recognizable face"
                )
                full_prompt = (
                    f"{style_anchor_start}"
                    f"a scene with exactly two characters: "
                    f"FIRST: {child_block}. "
                    f"SECOND: an animal companion - {char_part}. "
                    f"The animal is a separate creature, the animal wears no clothes. "
                    f"Only one human child in the image, no duplicate child. "
                    f"Scene: {prompt}, "
                    f"{style_prompt}, {clean_composition}"
                    f"{style_anchor_end}"
                )
            else:
                # 👤 רק הילד לבד
                outfit_clause = f"the child wearing {outfit_part}, " if outfit_part else ""
                full_prompt = (
                    f"{style_anchor_start}"
                    f"solo portrait of ONE single human child, "
                    f"exactly one child in the entire image, "
                    f"only one person, no duplicate figures, "
                    f"{trigger_word}, {outfit_clause}"
                    f"detailed facial features, recognizable face, expressive eyes, "
                    f"the child is the main focus of the scene, "
                    f"{prompt}, "
                    f"{style_prompt}, {clean_composition}"
                    f"{style_anchor_end}"
                )
            
            print(f"  🎨 Generating with LoRA...")
            print(f"  📝 Prompt: {full_prompt[:280]}...")
            
            # 🔄 Retry logic for rate limit (429) errors
            def _run_with_retry(model_target, input_params, max_retries=3):
                """מריץ replicate.run עם retry אוטומטי במקרה של rate limit"""
                last_error = None
                for attempt in range(max_retries):
                    try:
                        return replicate.run(model_target, input=input_params)
                    except Exception as e:
                        last_error = e
                        err_str = str(e).lower()
                        # אם זה rate limit - חכה ונסה שוב
                        if '429' in err_str or 'throttled' in err_str or 'rate limit' in err_str:
                            wait_time = 30 if attempt == 0 else 60
                            print(f"  ⏸️  Rate limit hit (attempt {attempt+1}/{max_retries}), waiting {wait_time}s...")
                            time.sleep(wait_time)
                            continue
                        # שגיאה אחרת - נזרק מיד
                        raise
                # אם הגענו לכאן - כל הניסיונות נכשלו
                raise last_error
            
            # 🎲 בניית input params - עם seed אם ניתן (לעקביות)
            base_input = {
                "num_outputs": 1,
                "aspect_ratio": "4:3",
                "output_format": "jpg",
                "guidance_scale": 3.5,
                "output_quality": 90,
                "num_inference_steps": 28,
                "disable_safety_checker": True
            }
            if seed is not None:
                base_input["seed"] = int(seed)
                print(f"  🎲 Using fixed seed: {seed}")
            
            # 🎯 STRATEGY 1 (Preferred): Use the trained model directly
            if lora_version:
                print(f"  📌 Using trained model directly (best quality)")
                strategy1_input = dict(base_input)
                strategy1_input["prompt"] = full_prompt
                strategy1_input["lora_scale"] = 1.0
                output = _run_with_retry(lora_version, strategy1_input)
            else:
                # 🔧 STRATEGY 2 (Fallback/Legacy): Use ostris/flux-dev-lora with weights URL
                print(f"  ⚠️  No version, using legacy ostris/flux-dev-lora")
                strategy2_input = dict(base_input)
                strategy2_input["prompt"] = full_prompt
                strategy2_input["lora_url"] = lora_url
                strategy2_input["lora_scale"] = 1.0
                output = _run_with_retry("ostris/flux-dev-lora", strategy2_input)
            
            if output and len(output) > 0:
                image_url = output[0]
                
                # Download
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                req = urllib.request.Request(
                    image_url,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                
                with urllib.request.urlopen(req, timeout=60, context=ctx) as response:
                    img_data = response.read()
                
                img_b64 = base64.b64encode(img_data).decode()
                print(f"  ✅ LoRA image generated! ({len(img_data)} bytes)")
                return f"data:image/jpeg;base64,{img_b64}"
            
            raise Exception("No output from LoRA generation")
            
        except Exception as e:
            print(f"  ❌ LoRA generation error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def handle_generate_pdf(self):
        """יוצר PDF עם תמונות ועברית - גרסה משופרת"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.lib.utils import simpleSplit, ImageReader
            from PIL import Image as PILImage
            
            try:
                from bidi.algorithm import get_display
                import arabic_reshaper
                has_bidi = True
            except:
                has_bidi = False
                print("  ⚠️ python-bidi/arabic-reshaper not available - Hebrew will be reversed!")
            
            def clean_text_for_pdf(text):
                """מנקה תווים מיוחדים שהפונט NotoSansHebrew לא תומך בהם"""
                if not text:
                    return text
                # מילון החלפות - תווים בעייתיים → תווים רגילים שיש בכל פונט
                replacements = {
                    # ציטוטים מתולתלים → ציטוטים רגילים
                    '\u201C': '"',  # left double quotation mark "
                    '\u201D': '"',  # right double quotation mark "
                    '\u2018': "'",  # left single quotation mark '
                    '\u2019': "'",  # right single quotation mark '
                    # גרש וגרשיים עבריים → תווים רגילים
                    '\u05F3': "'",  # Hebrew geresh
                    '\u05F4': '"',  # Hebrew gershayim
                    # נקודות, מקפים מיוחדים
                    '\u2026': '...',  # ellipsis
                    '\u2013': '-',    # en dash
                    '\u2014': '-',    # em dash
                    '\u00A0': ' ',    # non-breaking space
                    '\u200E': '',     # left-to-right mark (invisible)
                    '\u200F': '',     # right-to-left mark (invisible)
                    '\u2028': ' ',    # line separator
                    '\u2029': ' ',    # paragraph separator
                }
                for old, new in replacements.items():
                    text = text.replace(old, new)
                return text
            
            def fix_hebrew(text):
                """מסדר עברית בצורה נכונה לימין-לשמאל + ניקוי תווים בעייתיים"""
                # 🆕 ניקוי תווים מיוחדים לפני הכל
                text = clean_text_for_pdf(text)
                
                if not has_bidi:
                    return text
                try:
                    reshaped = arabic_reshaper.reshape(text)
                    return get_display(reshaped)
                except Exception as e:
                    print(f"  ⚠️ Hebrew fix failed: {e}")
                    return text
            
            def load_image_for_pdf(image_url):
                """מקבל URL של תמונה (יכול להיות base64 או http) ומחזיר ImageReader"""
                if not image_url:
                    return None
                try:
                    if image_url.startswith('data:image'):
                        # base64
                        header, b64data = image_url.split(',', 1)
                        img_bytes = base64.b64decode(b64data)
                    elif image_url.startswith('http'):
                        # הורד מ-URL
                        ctx = ssl.create_default_context()
                        ctx.check_hostname = False
                        ctx.verify_mode = ssl.CERT_NONE
                        req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req, timeout=30, context=ctx) as response:
                            img_bytes = response.read()
                    else:
                        return None
                    
                    img_buffer = BytesIO(img_bytes)
                    pil_img = PILImage.open(img_buffer)
                    # Convert to RGB if needed (for transparency issues)
                    if pil_img.mode in ('RGBA', 'LA', 'P'):
                        pil_img = pil_img.convert('RGB')
                    output = BytesIO()
                    pil_img.save(output, format='JPEG', quality=85)
                    output.seek(0)
                    return ImageReader(output)
                except Exception as e:
                    print(f"  ⚠️ Could not load image: {e}")
                    return None
            
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            story_data = json.loads(post_data.decode('utf-8'))
            
            child_name = story_data.get('childName', 'ילד')
            pages = story_data.get('pages', [])
            
            print(f"📄 PDF for: {child_name}")
            print(f"   Pages: {len(pages)}")
            print(f"   Hebrew support: {'✅' if has_bidi else '❌'}")
            
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            
            # 🇮🇱 NEW: הורדה אוטומטית של פונט עברי אמיתי מ-Google Fonts
            # זה מבטיח שעברית תיראה תקין ב-PDF, ולא ג'יבריש
            HEBREW_FONT_PATH = '/tmp/NotoSansHebrew-Regular.ttf'
            
            if not os.path.exists(HEBREW_FONT_PATH):
                try:
                    print(f"   🌐 Downloading Hebrew font from Google Fonts...")
                    font_url = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansHebrew/NotoSansHebrew-Regular.ttf"
                    
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    
                    req = urllib.request.Request(
                        font_url,
                        headers={'User-Agent': 'Mozilla/5.0'}
                    )
                    with urllib.request.urlopen(req, timeout=30, context=ctx) as response:
                        font_data = response.read()
                    
                    with open(HEBREW_FONT_PATH, 'wb') as f:
                        f.write(font_data)
                    print(f"   ✅ Hebrew font downloaded: {len(font_data)} bytes")
                except Exception as font_err:
                    print(f"   ⚠️ Failed to download Hebrew font: {font_err}")
            
            # Register Hebrew font - first try the downloaded one, then system fonts
            hebrew_font = 'Helvetica'
            font_paths = [
                HEBREW_FONT_PATH,  # 🥇 First try our downloaded font
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                '/usr/share/fonts/truetype/freefont/FreeSans.ttf',
                'C:\\Windows\\Fonts\\arial.ttf'
            ]
            
            for font_path in font_paths:
                try:
                    if os.path.exists(font_path):
                        pdfmetrics.registerFont(TTFont('Hebrew', font_path))
                        hebrew_font = 'Hebrew'
                        print(f"   📝 Font registered: {font_path}")
                        break
                except Exception as e:
                    print(f"   ⚠️ Font failed: {font_path} - {e}")
                    continue
            
            # ====== Cover Page ======
            c.setFillColorRGB(0.99, 0.96, 0.89)  # cream
            c.rect(0, 0, width, height, stroke=0, fill=1)
            c.setFillColorRGB(0.16, 0.13, 0.09)  # dark
            c.setFont(hebrew_font, 36)
            title = fix_hebrew(f"הספר של {child_name}")
            title_width = c.stringWidth(title, hebrew_font, 36)
            c.drawString((width - title_width) / 2, height - 200, title)
            
            c.setFont(hebrew_font, 16)
            subtitle = fix_hebrew("מבית לילוש טובוש")
            sub_width = c.stringWidth(subtitle, hebrew_font, 16)
            c.drawString((width - sub_width) / 2, height - 240, subtitle)
            c.showPage()
            
            # ====== Story Pages ======
            for i, page in enumerate(pages):
                print(f"   🖼️ Adding page {i+1}/{len(pages)}...")
                
                # Page number
                c.setFillColorRGB(0.36, 0.29, 0.21)
                c.setFont(hebrew_font, 10)
                page_num = fix_hebrew(f"עמוד {i + 1}")
                c.drawString(width - 100, 30, page_num)
                
                # ===== IMAGE =====
                image_url = page.get('imageUrl')
                if image_url:
                    img_reader = load_image_for_pdf(image_url)
                    if img_reader:
                        # Image position - top half of page
                        img_width = width - 80  # margin 40 each side
                        img_height = height * 0.55  # top 55% of page
                        img_x = 40
                        img_y = height - img_height - 60  # 60 from top
                        
                        try:
                            c.drawImage(
                                img_reader,
                                img_x, img_y,
                                width=img_width,
                                height=img_height,
                                preserveAspectRatio=True,
                                anchor='c'
                            )
                            print(f"      ✅ Image added")
                        except Exception as img_err:
                            print(f"      ⚠️ Image draw failed: {img_err}")
                
                # ===== TEXT =====
                c.setFillColorRGB(0.16, 0.13, 0.09)
                c.setFont(hebrew_font, 16)
                text = page.get('text', '')
                
                # Split and reverse for Hebrew (each line individually)
                if has_bidi and any(ord(ch) > 127 for ch in text):
                    # Hebrew: split, fix each line, then layout
                    raw_lines = simpleSplit(text, hebrew_font, 16, width - 100)
                    text_lines = [fix_hebrew(line) for line in raw_lines]
                else:
                    text_lines = simpleSplit(text, hebrew_font, 16, width - 100)
                
                # Text in bottom half
                y_position = height * 0.35  # ~35% from bottom
                for line in text_lines:
                    line_width = c.stringWidth(line, hebrew_font, 16)
                    c.drawString((width - line_width) / 2, y_position, line)
                    y_position -= 24
                
                c.showPage()
            
            c.save()
            
            pdf_data = buffer.getvalue()
            buffer.close()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/pdf')
            
            # 🔧 FIX: תמיכה בשמות קבצים בעברית ע"פ RFC 5987
            try:
                child_name.encode('latin-1')
                self.send_header('Content-Disposition', f'attachment; filename="lilush_{child_name}.pdf"')
            except UnicodeEncodeError:
                from urllib.parse import quote
                ascii_fallback = "lilush_book.pdf"
                utf8_filename = quote(f"lilush_{child_name}.pdf", safe='')
                self.send_header(
                    'Content-Disposition',
                    f'attachment; filename="{ascii_fallback}"; filename*=UTF-8\'\'{utf8_filename}'
                )
            
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
    print(f"👤 Face Swap: {'ON' if FAL_KEY and HAS_FAL else 'OFF'}")
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
