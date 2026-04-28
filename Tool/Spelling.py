import json
import difflib
from datetime import datetime, timedelta

class WordReviewSystem:
    def __init__(self, data_file='my_vocab.json'):
        self.data_file = data_file
        self.vocabulary = self._load_data()

    def _load_data(self):
        """Load data or initialize a new library."""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"words": {}, "prepositions": {}}

    def _save_data(self):
        """Save current state to JSON."""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.vocabulary, f, indent=4, ensure_ascii=False)

    # --- NEW: List Management ---
    def show_list(self, category):
        """Display all items in a category and return keys for indexing."""
        items = self.vocabulary.get(category, {})
        if not items:
            print(f"\nNo data found in {category}.")
            return []
        
        print(f"\n--- {category.upper()} LIST ---")
        print(f"{'ID':<4} {'Item':<18} {'Meaning':<15} {'Mastery'}")
        keys = list(items.keys())
        for idx, key in enumerate(keys, 1):
            meaning = items[key]['meaning']
            level = items[key]['level']
            print(f"{idx:<4} {key:<18} {meaning:<15} Lvl {level}")
        return keys

    def delete_item(self):
        """Delete an item by name or index."""
        print("\n--- 🗑️ Delete Item ---")
        print("1. Delete a Word")
        print("2. Delete a Preposition Phrase")
        cat_choice = input("Select category (1-2): ")
        category = "words" if cat_choice == '1' else "prepositions"
        
        keys = self.show_list(category)
        if not keys: return

        target = input("\nEnter [Word/Phrase] or [ID] to delete (or 'c' to cancel): ").strip().lower()
        if target == 'c': return

        # Check if input is a number (ID) or a string (Word)
        if target.isdigit():
            idx = int(target) - 1
            if 0 <= idx < len(keys):
                del_key = keys[idx]
            else:
                print("❌ Invalid ID.")
                return
        else:
            del_key = target

        if del_key in self.vocabulary[category]:
            del self.vocabulary[category][del_key]
            self._save_data()
            print(f"✅ Successfully deleted: {del_key}")
        else:
            print(f"❌ Item not found: {del_key}")

    # --- Adding Items ---
    def input_new_word(self):
        print("\n--- ➕ Add New Word ---")
        word = input("English word: ").strip().lower()
        meaning = input(f"Chinese meaning for '{word}': ").strip()
        if word and meaning:
            self.vocabulary["words"][word] = {
                "meaning": meaning, "level": 0,
                "next_review": datetime.now().strftime('%Y-%m-%d')
            }
            self._save_data()
            print(f"✅ Added '{word}'.")

    def input_new_preposition(self):
        print("\n--- ➕ Add Preposition Practice ---")
        phrase = input("Phrase base (e.g., 'depend'): ").strip()
        prep = input(f"Preposition for '{phrase}': ").strip().lower()
        meaning = input("Meaning: ").strip()
        if phrase and prep:
            key = f"{phrase} ___"
            self.vocabulary["prepositions"][key] = {
                "answer": prep, "meaning": meaning, "level": 0,
                "next_review": datetime.now().strftime('%Y-%m-%d')
            }
            self._save_data()
            print(f"✅ Added '{phrase} {prep}'.")

    # --- Review Engine ---
    def start_review(self):
        today = datetime.now().date()
        words_todo = [w for w, d in self.vocabulary["words"].items() 
                      if datetime.strptime(d['next_review'], '%Y-%m-%d').date() <= today]
        preps_todo = [p for p, d in self.vocabulary["prepositions"].items() 
                      if datetime.strptime(d['next_review'], '%Y-%m-%d').date() <= today]

        if not words_todo and not preps_todo:
            print("\n☕ Nothing to review today!")
            return

        for word in words_todo:
            data = self.vocabulary["words"][word]
            print(f"\n[Spelling] Meaning: {data['meaning']}")
            ans = input("Your answer: ").strip().lower()
            self._process_result("words", word, ans == word, word)

        for phrase in preps_todo:
            data = self.vocabulary["prepositions"][phrase]
            print(f"\n[Preposition] {phrase} ({data['meaning']})")
            ans = input("Fill gap: ").strip().lower()
            self._process_result("prepositions", phrase, ans == data['answer'], data['answer'])

        self._save_data()

    def _process_result(self, category, key, is_correct, correct_ans):
        item = self.vocabulary[category][key]
        if is_correct:
            print("✅ Correct!")
            item['level'] += 1
            days = 2 ** item['level']
        else:
            print(f"❌ Wrong! The correct answer is: {correct_ans}")
            item['level'] = 0
            days = 1
        item['next_review'] = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')

# --- Menu Interface ---
def main():
    system = WordReviewSystem()
    while True:
        print("\n" + "="*35)
        print("   VOCABULARY & PREP MANAGER")
        print("="*35)
        print("1. 🚀 Start Today's Review")
        print("2. ➕ Add New Word")
        print("3. 🔗 Add Preposition Phrase")
        print("4. 📋 View Library List")
        print("5. 🗑️  Delete an Item")
        print("6. ❌ Exit")
        
        cmd = input("\nChoose an option (1-6): ").strip()
        if cmd == '1': system.start_review()
        elif cmd == '2': system.input_new_word()
        elif cmd == '3': system.input_new_preposition()
        elif cmd == '4':
            print("\nWhat to view? 1. Words  2. Prepositions")
            c = input("Choice: ")
            system.show_list("words" if c == '1' else "prepositions")
        elif cmd == '5': system.delete_item()
        elif cmd == '6': break
        else: print("Invalid command.")

if __name__ == "__main__":
    main()
