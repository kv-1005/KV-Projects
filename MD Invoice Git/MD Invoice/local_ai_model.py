"""
Local AI Model Integration for Chatbot
Supports local transformer models for complete privacy and offline operation
"""

import os
import torch
from typing import Optional, Dict, List
import warnings
warnings.filterwarnings('ignore')

class LocalAIModel:
    """
    Local AI model wrapper for chatbot responses
    Supports multiple models: Phi-2, TinyLlama, Mistral, Llama-2
    """
    
    def __init__(self, model_name: str = None, device: str = None):
        """
        Initialize local AI model
        
        Args:
            model_name: Model to use (auto-detects if None)
            device: 'cuda' or 'cpu' (auto-detects if None)
        """
        self.model = None
        self.tokenizer = None
        self.device = device or self._detect_device()
        self.model_name = model_name or self._select_best_model()
        self._load_model()
    
    def _detect_device(self) -> str:
        """Auto-detect available device"""
        if torch.cuda.is_available():
            return 'cuda'
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return 'mps'  # Apple Silicon
        return 'cpu'
    
    def _select_best_model(self) -> str:
        """
        Select best model based on available resources
        Returns model path for Hugging Face
        """
        # Check available memory (rough estimate)
        try:
            import psutil
            available_gb = psutil.virtual_memory().available / (1024**3)
            
            if available_gb >= 14:
                return "mistralai/Mistral-7B-Instruct-v0.2"  # Best quality
            elif available_gb >= 8:
                return "microsoft/phi-2"  # Good balance
            elif available_gb >= 4:
                return "TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # Lightweight
            else:
                return "microsoft/phi-2"  # Default fallback
        except:
            # If psutil not available, use lightweight default
            return "microsoft/phi-2"
    
    def _load_model(self):
        """Load the transformer model and tokenizer"""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
            
            print(f"Loading local AI model: {self.model_name} on {self.device}...")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            # Configure quantization for memory efficiency
            quantization_config = None
            if self.device == 'cpu':
                # Use 8-bit quantization for CPU
                quantization_config = BitsAndBytesConfig(
                    load_in_8bit=True,
                    llm_int8_threshold=6.0
                ) if hasattr(BitsAndBytesConfig, 'load_in_8bit') else None
            
            # Load model
            model_kwargs = {
                "trust_remote_code": True,
                "torch_dtype": torch.float16 if self.device != 'cpu' else torch.float32,
            }
            
            if quantization_config:
                model_kwargs["quantization_config"] = quantization_config
            else:
                model_kwargs["low_cpu_mem_usage"] = True
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **model_kwargs
            )
            
            # Move to device
            if self.device != 'cpu' and not quantization_config:
                self.model = self.model.to(self.device)
            
            # Set to evaluation mode
            self.model.eval()
            
            print(f"✅ Model loaded successfully on {self.device}")
            
        except ImportError:
            print("❌ transformers library not installed. Install with: pip install transformers torch accelerate bitsandbytes")
            raise
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            print("💡 Try a smaller model or install required dependencies")
            raise
    
    def generate_response(
        self,
        user_message: str,
        system_prompt: str = "",
        conversation_history: Optional[List[Dict[str, str]]] = None,
        max_length: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> str:
        """
        Generate response using local model
        
        Args:
            user_message: User's question
            system_prompt: System instructions
            conversation_history: Previous messages
            max_length: Maximum response length
            temperature: Sampling temperature (0.1-1.0)
            top_p: Nucleus sampling parameter
        
        Returns:
            Generated response text
        """
        if not self.model or not self.tokenizer:
            return "Model not loaded. Please check your setup."
        
        try:
            # Build prompt
            prompt = self._build_prompt(user_message, system_prompt, conversation_history)
            
            # Tokenize
            inputs = self.tokenizer.encode(prompt, return_tensors="pt")
            if inputs.size(1) > 1024:  # Limit context length
                inputs = inputs[:, -1024:]  # Take last 1024 tokens
            
            inputs = inputs.to(self.device)
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=max_length,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.2,
                    num_return_sequences=1
                )
            
            # Decode response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the new response (remove prompt)
            if prompt in response:
                response = response.replace(prompt, "").strip()
            
            # Clean up response
            response = self._clean_response(response)
            
            return response if response else "I apologize, but I couldn't generate a response. Please try rephrasing your question."
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return f"Error generating response: {str(e)}"
    
    def _build_prompt(
        self,
        user_message: str,
        system_prompt: str,
        conversation_history: Optional[List[Dict[str, str]]]
    ) -> str:
        """Build prompt from user message and context"""
        
        # Default system prompt if none provided
        if not system_prompt:
            system_prompt = """You are MD, an advanced, highly intelligent AI assistant with comprehensive knowledge across all domains. 
You can answer questions about invoices, business, technology, science, general knowledge, and anything else.
Be helpful, accurate, and provide detailed, well-structured responses."""
        
        # Build conversation context
        context = system_prompt + "\n\n"
        
        if conversation_history:
            for msg in conversation_history[-5:]:  # Last 5 messages
                role = "User" if msg['role'] == 'user' else "Assistant"
                context += f"{role}: {msg['message']}\n"
        
        context += f"User: {user_message}\nAssistant:"
        
        return context
    
    def _clean_response(self, response: str) -> str:
        """Clean and format the generated response"""
        # Remove excessive whitespace
        response = ' '.join(response.split())
        
        # Remove common artifacts
        response = response.replace("User:", "").replace("Assistant:", "").strip()
        
        # Limit length
        if len(response) > 1000:
            # Try to cut at sentence boundary
            sentences = response.split('. ')
            response = '. '.join(sentences[:5]) + '.'
        
        return response.strip()
    
    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model is not None and self.tokenizer is not None


# Fine-tuning support (optional, for advanced users)
class ModelFineTuner:
    """
    Fine-tuning support for custom domain training
    Requires additional setup and training data
    """
    
    @staticmethod
    def prepare_training_data(conversations: List[Dict]) -> str:
        """
        Prepare conversation data for fine-tuning
        
        Args:
            conversations: List of conversation dictionaries
        
        Returns:
            JSONL formatted string for training
        """
        training_data = []
        for conv in conversations:
            messages = conv.get('messages', [])
            formatted = {
                "messages": [
                    {"role": msg['role'], "content": msg['message']}
                    for msg in messages
                ]
            }
            training_data.append(formatted)
        
        # Convert to JSONL format
        import json
        return '\n'.join(json.dumps(item) for item in training_data)
    
    @staticmethod
    def fine_tune_with_lora(
        model_name: str,
        training_data_path: str,
        output_dir: str = "./fine_tuned_model"
    ):
        """
        Fine-tune model using LoRA (Low-Rank Adaptation)
        Requires: pip install peft datasets
        
        Args:
            model_name: Base model to fine-tune
            training_data_path: Path to training data (JSONL)
            output_dir: Where to save fine-tuned model
        """
        try:
            from peft import LoraConfig, get_peft_model, TaskType
            from transformers import TrainingArguments, Trainer, AutoModelForCausalLM
            
            print("Fine-tuning model with LoRA...")
            print("This is an advanced feature. See documentation for full setup.")
            
            # LoRA configuration
            lora_config = LoraConfig(
                task_type=TaskType.CAUSAL_LM,
                inference_mode=False,
                r=8,
                lora_alpha=32,
                lora_dropout=0.1
            )
            
            # Load model
            model = AutoModelForCausalLM.from_pretrained(model_name)
            model = get_peft_model(model, lora_config)
            
            print("Fine-tuning setup complete. Use Hugging Face Trainer for actual training.")
            return model
            
        except ImportError:
            print("Fine-tuning requires: pip install peft datasets")
            raise


# Usage example and integration
if __name__ == "__main__":
    # Example usage
    print("Local AI Model Test")
    print("=" * 50)
    
    try:
        # Initialize model
        local_ai = LocalAIModel()
        
        if local_ai.is_loaded():
            # Test query
            response = local_ai.generate_response(
                "What is the boiling point of water?",
                temperature=0.7
            )
            print(f"Response: {response}")
        else:
            print("Model not loaded. Check dependencies.")
            
    except Exception as e:
        print(f"Error: {e}")
        print("\nTo use local AI models, install dependencies:")
        print("pip install torch transformers accelerate bitsandbytes")

