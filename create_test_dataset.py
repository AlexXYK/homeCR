"""
Create a simple test dataset with sample data.
Run this to set up initial test cases.
"""
from pathlib import Path

# Create test dataset structure
test_datasets = {
    "print": {
        "sample1": "This is a test document with printed text.\nSecond line of text.",
        "sample2": "Invoice #12345\nDate: 2024-01-15\nTotal: $99.99",
    },
    "handwriting": {
        "sample1": "This is handwritten text\nwith multiple lines",
    },
    "tables": {
        "sample1": """| Name | Age | City |
|------|-----|------|
| John | 25 | NYC |
| Jane | 30 | LA |""",
    },
    "mixed": {
        "sample1": "Document Title\n\nThis paragraph contains printed text.\n\n[Handwritten note: Remember to follow up]",
    }
}

def create_test_datasets():
    """Create test dataset directories and ground truth files."""
    base_path = Path("data/test_datasets")
    
    for category, samples in test_datasets.items():
        images_dir = base_path / category / "images"
        gt_dir = base_path / category / "ground_truth"
        
        images_dir.mkdir(parents=True, exist_ok=True)
        gt_dir.mkdir(parents=True, exist_ok=True)
        
        for sample_id, ground_truth in samples.items():
            # Save ground truth
            gt_file = gt_dir / f"{sample_id}.txt"
            gt_file.write_text(ground_truth, encoding='utf-8')
            print(f"✓ Created: {gt_file}")
    
    print("\n" + "="*60)
    print("📁 Test dataset structure created!")
    print("="*60)
    print("\nNext steps:")
    print("1. Add real images to data/test_datasets/*/images/")
    print("2. Match filenames with ground truth files")
    print("3. Run: py run_tests.py --dataset print")
    print("="*60)

if __name__ == "__main__":
    create_test_datasets()

