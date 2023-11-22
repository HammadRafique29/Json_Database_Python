import cmd
import json
import os
import re

class MyLib:
    def __init__(self):
        self.data_files = []
        self.current_data = None
        self.current_file = None

    def create_dataset(self, filename, data=None):
        filename += '.json'
        if os.path.exists(filename):
            return f"File {filename} already exists!"

        with open(filename, 'w') as file:
            json.dump(data if data else [], file)

        self.data_files.append(filename)
        return f"Dataset {filename} created."

    def load_dataset(self, filename):
        filename += '.json'
        if not os.path.exists(filename):
            return f"File {filename} not found!"

        with open(filename, 'r') as file:
            self.current_data = json.load(file)
            self.current_file = filename

        return f"Dataset {filename} loaded."

    def add_record(self, record):
        if self.current_data is None:
            return "No dataset loaded. Load a dataset first."
        
        if any(existing_record['title'] == record['title'] for existing_record in self.current_data):
        	return "Record with this title already exists."
        
        self.current_data.append(record)
        self.save_dataset()
        return f"Record added: {json.dumps(record)}"

    def save_dataset(self):
        if self.current_file and self.current_data is not None:
            with open(self.current_file, 'w') as file:
                json.dump(self.current_data, file)

    def find_books(self, field, value, operator):
        if self.current_data is None:
            return "No dataset loaded. Load a dataset first."

        try:
            value = float(value)  # Attempt to convert the value to a number for comparison
        except ValueError:
            pass  # If conversion fails, keep it as a string

        # Applying different conditions based on the operator
        if operator == '=':
            matched_books = [record for record in self.current_data if record.get(field) == value]
        elif operator == '>=':
            matched_books = [record for record in self.current_data if record.get(field) >= value]
        elif operator == '>':
            matched_books = [record for record in self.current_data if record.get(field) > value]
        elif operator == '<':
            matched_books = [record for record in self.current_data if record.get(field) < value]
        elif operator == '<=':
            matched_books = [record for record in self.current_data if record.get(field) <= value]
        else:
            return "Invalid operator."

        if not matched_books:
            return f"No books found with {field} {operator} {value}"

        return json.dumps(matched_books, indent=4)
        
    def update_record(self, field, new_value, condition_field, condition_operator, condition_value):
        if self.current_data is None:
            return "No dataset loaded. Load a dataset first."

        try:
            condition_value = float(condition_value)  # Convert to a number for comparison, if applicable
        except ValueError:
            pass  # If conversion fails, keep it as a string

        operators = {
            '=': lambda x: x.get(condition_field) == condition_value,
            '>': lambda x: x.get(condition_field) > condition_value,
            '<': lambda x: x.get(condition_field) < condition_value,
            '>=': lambda x: x.get(condition_field) >= condition_value,
            '<=': lambda x: x.get(condition_field) <= condition_value
        }

        if condition_operator not in operators:
            return "Invalid condition operator."

        updated = False
        for record in self.current_data:
            if operators[condition_operator](record):
                # Adding a check to ensure the field exists in the record before updating
                if field in record:
                    record[field] = new_value
                    updated = True
                else:
                    return f"Field {field} not found in the record."

        if updated:
            self.save_dataset()

        return "Record updated successfully." if updated else f"No record found with {condition_field} {condition_operator} {condition_value}"

    def delete_record(self, condition_field, condition_operator, condition_value):
        if self.current_data is None:
            return "No dataset loaded. Load a dataset first."

        try:
            condition_value = float(condition_value)  # Convert to number for comparison if applicable
        except ValueError:
            pass

        operators = {
            '=': lambda x: x.get(condition_field) == condition_value,
            '>': lambda x: x.get(condition_field) > condition_value,
            '<': lambda x: x.get(condition_field) < condition_value,
            '>=': lambda x: x.get(condition_field) >= condition_value,
            '<=': lambda x: x.get(condition_field) <= condition_value
        }

        if condition_operator not in operators:
            return "Invalid condition operator."

        # Get the filtered data
        filtered_data = list(filter(operators[condition_operator], self.current_data))
        
        if not filtered_data:
            return "No books match the provided condition."
        
        # Delete the books that match the condition
        self.current_data = [x for x in self.current_data if x not in filtered_data]

        # Save the updated dataset
        self.save_dataset()
        
        return f"books matching {condition_field} {condition_operator} {condition_value} have been deleted."

    def sort_by(self, field, condition_field=None, condition_operator=None, condition_value=None, order='ASC'):
        if self.current_data is None:
            return "No dataset loaded. Load a dataset first."
        
        # Check if the order parameter is valid
        if order.upper() not in ['ASC', 'DESC']:
            return "Invalid order type. Use ASC or DESC."
        
        filtered_data = self.current_data
        
        # If a condition is provided, filter the data first before sorting
        if condition_field and condition_operator and condition_value:
            try:
                condition_value = float(condition_value)  # Convert to a number for comparison, if applicable
            except ValueError:
                pass
            
            operators = {
                '=': lambda x: x.get(condition_field) == condition_value,
                '>': lambda x: x.get(condition_field) > condition_value,
                '<': lambda x: x.get(condition_field) < condition_value,
                '>=': lambda x: x.get(condition_field) >= condition_value,
                '<=': lambda x: x.get(condition_field) <= condition_value
            }
            
            if condition_operator not in operators:
                return "Invalid condition operator."
            
            filtered_data = list(filter(operators[condition_operator], self.current_data))
            
            if not filtered_data:
                return "No books match the provided condition."
        
        # Sort the filtered data based on the order type
        if field in ["pages", "isbn"]:
            sorted_data = sorted(filtered_data, key=lambda x: x.get(field), reverse=(order.upper() == "ASC"))
        else: sorted_data = sorted(filtered_data, key=lambda x: x.get(field), reverse=(order.upper() == "DESC"))
        
        return json.dumps(sorted_data, indent=4)

    def join(self, other_dataset, field):
        if self.current_data is None:
            return "No dataset loaded. Load a dataset first."

        if not os.path.exists(other_dataset + '.json'):
            return f"File {other_dataset}.json not found!"

        with open(other_dataset + '.json', 'r') as file:
            other_data = json.load(file)

        joined_data = {}

        # Add records from the first dataset
        for record in self.current_data:
            key_value = record.get(field)
            if key_value not in joined_data:
                joined_data[key_value] = {'self': [], 'other': []}
            joined_data[key_value]['self'].append(record)

        # Add records from the second dataset
        for record in other_data:
            key_value = record.get(field)
            if key_value not in joined_data:
                joined_data[key_value] = {'self': [], 'other': []}
            joined_data[key_value]['other'].append(record)

        return json.dumps(joined_data, indent=4)

    def count(self, field, operator, value):
        
        if self.current_data is None:
            return "No dataset loaded. Load a dataset first."
        
        print(field, operator, value)
        count = 0
        if operator==None and value==None and field==None:
            for row in self.current_data:
                count += 1
            return f"Total Records {count}"
        else:
            for row in self.current_data:
                if operator == "=": 
                    if str(row[field]) == value: count += 1
                elif operator == ">=": 
                    if str(row[field]) >= value: count += 1
                elif operator == "<=": 
                    if str(row[field]) <= value: count += 1
                elif operator == "!=": 
                    if str(row[field]) != value: count += 1
                else: continue
                
            return f"Total Records {count}"
            
    def sum(self, field, operator, value):
        
        if self.current_data is None:
            return "No dataset loaded. Load a dataset first."
        
        sum_pages = 0
        if operator==None and value==None and field==None:
            for row in self.current_data:
                sum_pages += row["pages"]
            return f"Total Pages {sum_pages}"
        else:
            for row in self.current_data:
                if operator == "=": 
                    if str(row[field]) == value: sum_pages += row["pages"]
                elif operator == ">=": 
                    if str(row[field]) >= value: sum_pages += row["pages"]
                elif operator == "<=": 
                    if str(row[field]) <= value: sum_pages += row["pages"]
                elif operator == "!=": 
                    if str(row[field]) != value: sum_pages += row["pages"]
                else: continue
                
            return f"Total Pages {sum_pages}"
        
    def average(self, field, operator, value):
        if self.current_data is None:
            return "No dataset loaded. Load a dataset first."
        
        page_average = 0
        publishedYear_average = 0
        count = 0

        if operator==None and value==None and field==None:
            for row in self.current_data:
                publishedYear_average += row["publishedYear"]
                page_average += row["pages"]
                count += 1
        else:
            for row in self.current_data:
                if operator == "=": 
                    if str(row[field]) == value: 
                        publishedYear_average += int(row["publishedYear"])
                        page_average += int(row["pages"])
                elif operator == ">=": 
                    if str(row[field]) >= value: 
                        publishedYear_average += int(row["publishedYear"])
                        page_average += int(row["pages"])
                elif operator == "<=": 
                    if str(row[field]) <= value: 
                        publishedYear_average += int(row["publishedYear"])
                        page_average += int(row["pages"])
                elif operator == "!=": 
                    if str(row[field]) != value: 
                        publishedYear_average += int(row["publishedYear"])
                        page_average += int(row["pages"])
                else: continue
                count += 1
            
        page_average = page_average/count
        publishedYear_average = publishedYear_average/count
            
        return f"--- Page AVG: {page_average}\t\n--- Published Year AVG: {publishedYear_average}"  

    def Max(self):
        if self.current_data is None:
            return "No dataset loaded. Load a dataset first."
        
        maximum = 0
        for row in self.current_data:
            if row["pages"] > maximum: maximum = row["pages"]
        return f"--- Book With Maximum Pages: {maximum}"
    
    def minimum(self):
        if self.current_data is None:
            return "No dataset loaded. Load a dataset first."
        
        minimum = self.current_data[0]["pages"]
        for row in self.current_data:
            if row["pages"] < minimum: minimum = row["pages"]
        return f"--- Book With Miimum Pages: {minimum}"

class MyLibShell(cmd.Cmd):
    intro = 'Welcome to the MyLib shell. Type help or ? to list commands.\n'
    prompt = 'MyLib > '

    def __init__(self):
        super(MyLibShell, self).__init__()
        self.db = MyLib()

    def do_create(self, arg):
        """Create a new dataset: CREATE <filename>"""
        if not arg:
            print("Usage: CREATE <filename>")
            return
        print(self.db.create_dataset(arg))

    def do_load(self, arg):
        """Load a dataset: LOAD <filename>"""
        if not arg:
            print("Usage: LOAD <filename>")
            return
        print(self.db.load_dataset(arg))

    def do_add(self, arg):
        """Add a new record: ADD <record_as_json>"""
        if not arg:
            print("Usage: ADD <record_as_json>")
            return
        try:
            record = json.loads(arg)
            print(self.db.add_record(record))
        except json.JSONDecodeError:
            print("Invalid JSON format.")

    def do_find(self, line):
        """Find books with a specific condition, e.g., FIND books whose age is 30"""
        if self.db.current_data is None:
            print("No dataset loaded. Load a dataset first.")
            return

        try:
            # Extracting condition from the line
            condition = re.search(r"books whose (.+)", line)
            if condition:
                condition = condition.group(1).strip()
                operator = None
                
                if 'at least' in condition:
                    field, _, value = condition.partition(' at least ')
                    operator = '>='
                elif 'is' in condition:
                    field, _, value = condition.partition(' is ')
                    operator = '='
                elif 'greater than' in condition:
                    field, _, value = condition.partition(' greater than ')
                    operator = '>'
                elif 'less than' in condition:
                    field, _, value = condition.partition(' less than ')
                    operator = '<'
                elif 'at most' in condition:
                    field, _, value = condition.partition(' at most ')
                    operator = '<='
                else:
                    print("Invalid condition format.")
                    return
                
                results = self.db.find_books(field.strip(), value.strip(), operator)
                print("Matching books:")
                print(results)
            else:
                print("Invalid query format. Use: FIND books whose <condition>")
        except Exception as e:
            print(f"Error executing find: {e}")

    def do_update(self, line):
        args = line.split()
        if len(args) < 5:
            print("Usage: UPDATE <field> = <new_value> WHERE <condition_field> = <condition_value>")
            return

        try:
            if self.db.current_data is None:
                print("No dataset loaded. Load a dataset first.")
                return
            
            pattern = re.compile(r'(\w+) = (.*?) WHERE (\w+) = (.*?)$')
            match = pattern.match(line.strip())
            if not match:
                print("Invalid update format. Use: UPDATE <field> = <value> WHERE <condition_field> = <condition_value>")
                return
            
            update_field, update_value, condition_field, condition_value = match.groups()
            update_value = update_value.strip(' "')
            condition_value = condition_value.strip(' "')
            
            updated_count = 0
            for record in self.db.current_data:
                if str(record.get(condition_field)) == condition_value:
                    if update_value.isdigit():
                        update_value = int(update_value)
                    record[update_field] = update_value
                    updated_count += 1
            
            if updated_count == 0:
                print("No books updated.")
                return
            
            self.db.save_dataset()
            print(f"{updated_count} books updated.")
        except Exception as e:
            print(f"Error updating books: {e}")

    def do_delete(self, line):
        """
        Delete books with a specific condition: 
        DELETE WHERE <condition_field> <condition_operator> <condition_value>
        """
        
        args = line.split()
        if args[1] not in ["pages", "isbn", "publishedYear", "publishedDate"]: 
            args[3] = " ".join(args[3:])
            args = args[:4]
            
        print(args)
        if len(args) != 4 or args[0].upper() != 'WHERE':
            print("Usage: DELETE WHERE <condition_field> <condition_operator> <condition_value>")
            return

        condition_field = args[1]
        condition_operator = args[2]
        condition_value = args[3]

        print(len(line.split()))
        
        print(self.db.delete_record(condition_field, condition_operator, condition_value))

    def do_sortby(self, line):
        """
        Sort books by a specific attribute in ascending or descending order 
        based on a given condition: 
        SORTBY <field> [ASC|DESC] WHERE <condition_field> <condition_operator> <condition_value>
        """
        args = line.split()
        if len(args) not in [1, 2, 6] or (len(args) == 6 and args[2].upper() != 'WHERE'):
            print("Usage: SORTBY <field> [order] WHERE <condition_field> <condition_operator> <condition_value>")
            return
        
        field = args[0]
        try: order = args[1]
        except: order = 'ASC'
    
        condition_field = condition_operator = condition_value = None
        
        if len(args) > 2:
            order = args[1]
            condition_field = args[3]
            condition_operator = args[4]
            condition_value = args[5]
        
        print(self.db.sort_by(field, condition_field, condition_operator, condition_value, order))

    def do_join(self, line):
        # """Join current data with another dataset by a specific field: JOIN <other_dataset> <field>"""
        args = line.split()
        if len(args) != 2:
            print("Usage: JOIN <other_dataset> <field>")
            return
        other_dataset, field = args
        print("Joined Data:")
        print(self.db.join(other_dataset, field))

    def do_count(self, line):
        args = line.split()

        field=None, 
        operator = None,
        value = None
        
        try: 
            field = field[0]
            operator = operator[0]
        except: pass
        
        if len(args) == 1:
            pass
        elif len(args) == 5:
            field, operator, value = args[2], args[3], args[4]
        else:
            print("Usage: COUNT book WHERE <condition_field> <condition_operator> <condition_value>")
            return
        
        print(self.db.count(field, operator, value))

    def do_sum(self, line):
        args = line.split()

        field=None, 
        operator = None,
        value = None
        
        try: 
            field = field[0]
            operator = operator[0]
        except: pass
        
        if len(args) == 1:
            pass
        elif len(args) == 5:
            field, operator, value = args[2], args[3], args[4]
        elif len(args) > 5:
            field, operator, value = args[2], args[3], ' '.join(args[4:])
        else:
            print("Usage: SUM book WHERE <condition_field> <condition_operator> <condition_value>")
            return
        
        print(self.db.sum(field, operator, value))
    
    def do_average(self, line):
        args = line.split()

        field= None, 
        operator = None,
        value = None
        
        try: 
            field = field[0]
            operator = operator[0]
        except: pass
        
        if len(args) == 1:
            pass
        elif len(args) == 5:
            field, operator, value = args[2], args[3], args[4]
            print(field, operator, value)
        elif len(args) > 5:
            field, operator, value = args[2], args[3], ' '.join(args[4:])
            print(field, operator, value)
        else:
            print("Usage: AVERAGE book WHERE <condition_field> <condition_operator> <condition_value>")
            return

        print(self.db.average(field, operator, value))
    
    def do_max(self, line):
        args = line.split()

        field= None, 
        
        try: 
            field = field[0]
        except: pass
        
        if len(args) == 1:
            pass
        else:
            print("Usage: MAX book")
            return

        print(self.db.Max())
    
    def do_min(self, line):
        args = line.split()

        field= None, 
        try: 
            field = field[0]
        except: pass
        
        if len(args) == 1:
            pass
        else:
            print("Usage: MIN book")
            return

        print(self.db.minimum())
            
    def do_exit(self, line):
        """Exit the shell"""
        print("Exiting...")
        return True

if __name__ == '__main__':
    MyLibShell().cmdloop()
