import os, glob, re, shutil
base_dir = r'c:\Users\abhin\Desktop\ophilliaHRMS\services\attendance-service\app\db\migrations'
files = glob.glob(os.path.join(base_dir, '001*.py'))

for f in sorted(files):
    with open(f, 'r') as file:
        content = file.read()
    
    # Extract the number part from filename, e.g., 0010
    num_str = os.path.basename(f)[:4]
    new_rev = f'm{num_str[1:]}'
    
    # Fix revision
    content = re.sub(r'revision\s*=\s*\".*?\"', f'revision = "{new_rev}"', content)
    
    # Fix down_revision
    if num_str == '0010':
        content = re.sub(r'down_revision\s*=\s*None', 'down_revision = "0013"', content)
    else:
        prev_num_str = f'{int(num_str) - 1:04d}'
        prev_rev = f'm{prev_num_str[1:]}'
        content = re.sub(r'down_revision\s*=\s*\".*?\"', f'down_revision = "{prev_rev}"', content)
    
    # Write back
    with open(f, 'w') as file:
        file.write(content)
        
    # Move to versions/
    shutil.move(f, os.path.join(base_dir, 'versions', os.path.basename(f).replace(num_str, new_rev)))

print('Done migrating scripts.')
