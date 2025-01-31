import pandas as pd
import yaml
import re

def parse_text_file(filename):
    """ Reads the text file and extracts modbus-related data into a pandas DataFrame. """
    with open(filename, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    start_index = None
    for i, line in enumerate(lines):
        if "#BEGIN ELEMENT_DOC" in line:
            start_index = i + 1
            break
    
    if start_index is None:
        raise ValueError("BEGIN ELEMENT_DOC not found in file")

    data = []
    for line in lines[start_index:]:
        if "#END" in line:
            break
        parts = [p.strip('"') for p in line.strip().split('","')]
        if len(parts) == 5:
            data.append(parts)
    
    df = pd.DataFrame(data, columns=["source element", "flags", "nickname", "extra info", "description"])
    return df

def generate_yaml(df):
    """ Filters modbus-related elements and converts them into a structured YAML format. """
    yaml_structure = {
        "Name": "Tags",
        "Type": "FolderType",
        "Children": []
    }

    for _, row in df.iterrows():
        source = row["source element"]
        nickname = row["nickname"]

        match = re.match(r"(MC|MHR)(\d+)(:RD)?", source)
        if match:
            prefix, number, rd_flag = match.groups()
            number = int(number)
            
            if not rd_flag:
                number -= 1 # Float/Real 32 bit values in the PLCs modbus server are referenced by the later address (real in plc at 69,70 | ref in optix as 70 - 1 = 69)

            tag_entry = {
                "Name": nickname,
                "Type": "ModbusTag",
                "DataType": "Float" if rd_flag else ("Int16" if prefix == "MHR" else "Boolean"),
                "Children": [
                    {
                        "Name": "NumRegister" if prefix == "MHR" else "NumCoil",
                        "Type": "BaseDataVariableType",
                        "DataType": "UInt16",
                        "Value": number
                    },
                    {
                        "Name": "MemoryArea",
                        "Type": "BaseDataVariableType",
                        "DataType": "ModbusMemoryArea"
                    }
                ]
            }
            yaml_structure["Children"].append(tag_entry)

    return yaml.dump(yaml_structure, sort_keys=False, default_flow_style=False)

if __name__ == "__main__":
    filename = "C:\\Users\\admin\\Desktop\\EPCOT1 PLC\\EPCOT1_EXPORT_DMD.txt"  # Change this to your actual file path
    df = parse_text_file(filename)
    yaml_output = generate_yaml(df)
    
    with open("Tags.yaml", "w", encoding="utf-8") as yaml_file:
        yaml_file.write(yaml_output)
    
    print("YAML file generated: modbus_tags.yaml")
