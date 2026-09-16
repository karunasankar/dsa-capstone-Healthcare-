import glob

files = glob.glob('src/pages/*.jsx')
for f in files:
    with open(f, 'r') as file:
        content = file.read()
    
    if 'const [error, setError]' not in content and 'useState(null)' in content:
        content = content.replace('useState(null);', 'useState(null);\n    const [error, setError] = useState(null);', 1)
        content = content.replace('catch(err => console.error(err));', 'catch(err => setError(err.message || "Failed to load data"));')
        
        # Dashboard, Integrity, Blockchain have this
        content = content.replace(
            'return <div>Loading...</div>;',
            'if (error) return <div className="p-6 text-red-500 font-bold">API Error: {error}</div>;\n    return <div>Loading...</div>;'
        )
        
    with open(f, 'w') as file:
        file.write(content)
