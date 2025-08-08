import requests
import json

def interactive_chatbot():
    """Interactive chatbot for Islamic Center of Frisco"""
    url = "http://127.0.0.1:5000/ask"
    
    print("🕌 Islamic Center of Frisco Chatbot")
    print("=" * 50)
    print("Ask me anything about ICF! Type 'quit' or 'exit' to stop.")
    print("=" * 50)
    
    # Test API health first
    try:
        health_response = requests.get("http://127.0.0.1:5000/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Connected to ICF chatbot successfully!\n")
        else:
            print("❌ API health check failed")
            return
    except:
        print("❌ Cannot connect to chatbot API.")
        print("💡 Make sure to start the server first: python ollamaLLM.py\n")
        return
    
    history = []
    
    while True:
        # Get user question
        print("🙋 You:", end=" ")
        question = input().strip()
        
        # Check for exit commands
        if question.lower() in ['quit', 'exit', 'bye', 'goodbye']:
            print("🤖 Chatbot: Thank you for visiting! May Allah bless you. 🤲")
            break
        
        if not question:
            print("🤖 Chatbot: Please ask me a question about the Islamic Center of Frisco!\n")
            continue
        
        # Send question to API
        data = {
            "question": question,
            "history": history
        }
        
        try:
            print("🤖 Chatbot: ", end="", flush=True)
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"{result['answer']}")
                
                # Show context info (optional)
                chunks_found = result.get('context_chunks_found', 0)
                if chunks_found > 0:
                    print(f"   📚 (Found {chunks_found} relevant information sources)")
                else:
                    print("   ❓ (No specific information found in our database)")
                
                # Update conversation history
                history = result['history']
                
            else:
                print(f"❌ Sorry, I encountered an error: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Sorry, I couldn't process your request: {e}")
        
        print()  # Add blank line for readability

def quick_test():
    """Quick test with sample questions"""
    url = "http://127.0.0.1:5000/ask"
    
    sample_questions = [
        "When was ICF established?",
        "Tell me about the Sunday School program",
        "What health services do you offer?",
        "How many students are in Sunday School?"
    ]
    
    print("🧪 Quick Test Mode - Sample Questions")
    print("=" * 40)
    
    # Test API health
    try:
        health_response = requests.get("http://127.0.0.1:5000/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ API not responding")
            return
    except:
        print("❌ Cannot connect to API. Start server with: python ollamaLLM.py")
        return
    
    for i, question in enumerate(sample_questions, 1):
        print(f"\n{i}. 🙋 Question: {question}")
        
        data = {"question": question, "history": []}
        
        try:
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"   🤖 Answer: {result['answer']}")
                print(f"   📊 Context chunks: {result.get('context_chunks_found', 0)}")
            else:
                print(f"   ❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")

def test_specific_content():
    """Test with content from your specific chunk"""
    url = "http://127.0.0.1:5000/ask"
    
    print("🎯 Testing Specific ICF Content")
    print("=" * 35)
    
    # Questions based on your chunk content
    specific_questions = [
        "When was the Islamic Center of Frisco established?",
        "How many volunteers run the Sunday School?", 
        "How many students are in Sunday School and how many are on the waitlist?",
        "What does the Safwah Youth Seminary program focus on?",
        "Tell me about the free health clinic",
        "What is the Uswah Adult Seminary program?",
        "Where is ICF located relative to downtown Dallas?",
        "What programs does the Quran Academy offer?"
    ]
    
    try:
        requests.get("http://127.0.0.1:5000/health", timeout=5)
    except:
        print("❌ Server not running. Start with: python ollamaLLM.py")
        return
    
    for question in specific_questions:
        print(f"\n🙋 Q: {question}")
        
        data = {"question": question, "history": []}
        
        try:
            response = requests.post(url, json=data, timeout=300)
            if response.status_code == 200:
                result = response.json()
                print(f"🤖 A: {result['answer']}")
            else:
                print("❌ Error occurred")
        except:
            print("❌ Request failed")
        
        input("   Press Enter for next question...")

if __name__ == "__main__":
    print("Islamic Center of Frisco Chatbot Test")
    print("=" * 40)
    
    while True:
        print("\nSelect mode:")
        print("1. 💬 Interactive Chatbot (type your own questions)")
        print("2. 🧪 Quick Test (sample questions)")
        print("3. 🎯 Test Specific Content (your chunk data)")
        print("4. 🚪 Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            interactive_chatbot()
        elif choice == "2":
            quick_test()
        elif choice == "3":
            test_specific_content()
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Please enter 1, 2, 3, or 4")
