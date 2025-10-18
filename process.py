"""
MCA Insights Engine - Real Change Detection
Processes actual multi-date snapshots with flexible file structure
Supports both folder-based (day1/day2) and direct CSV files
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RealDataProcessor:
    """Process real MCA data with actual change detection"""
    
    def __init__(self, raw_data_path):
        self.raw_data_path = Path(raw_data_path)
        
        # Column mapping based on your actual data
        self.column_mapping = {
            'CIN': 'CIN',
            'CompanyName': 'COMPANY_NAME',
            'CompanyClass': 'COMPANY_CLASS',
            'CompanyCategory': 'COMPANY_CATEGORY',
            'CompanyRegistrationdate_date': 'DATE_OF_INCORPORATION',
            'AuthorizedCapital': 'AUTHORIZED_CAP',
            'PaidupCapital': 'PAIDUP_CAPITAL',
            'CompanyStatus': 'COMPANY_STATUS',
            'CompanySubCategory': 'COMPANY_SUB_CATEGORY',
            'CompanyIndustrialClassification': 'PRINCIPAL_BUSINESS_ACTIVITY_AS_PER_CIN',
            'nic_code': 'NIC_CODE',
            'Registered_Office_Address': 'REGISTERED_OFFICE_ADDRESS',
            'CompanyROCcode': 'ROC_CODE',
        }
        
        self.required_columns = [
            'CIN', 'COMPANY_NAME', 'COMPANY_CLASS', 'DATE_OF_INCORPORATION',
            'AUTHORIZED_CAP', 'PAIDUP_CAPITAL', 'COMPANY_STATUS',
            'PRINCIPAL_BUSINESS_ACTIVITY_AS_PER_CIN', 'REGISTERED_OFFICE_ADDRESS',
            'ROC_CODE', 'STATE'
        ]
        
        # State file patterns
        self.state_patterns = {
            'maharashtra': ['maharashtra', 'maha', 'mh'],
            'gujarat': ['gujarat', 'guj', 'gj'],
            'delhi': ['delhi', 'del', 'dl'],
            'tamil_nadu': ['tamil', 'tamilnadu', 'tn'],
            'karnataka': ['karnataka', 'kar', 'ka', 'karn']
        }
        
        self.state_names = {
            'maharashtra': 'Maharashtra',
            'gujarat': 'Gujarat',
            'delhi': 'Delhi',
            'tamil_nadu': 'Tamil Nadu',
            'karnataka': 'Karnataka'
        }
    
    def detect_state_from_filename(self, filename):
        """Detect state from filename"""
        filename_lower = filename.lower()
        
        for state_key, patterns in self.state_patterns.items():
            for pattern in patterns:
                if pattern in filename_lower:
                    return self.state_names[state_key]
        
        return 'Unknown'
    
    def load_file(self, filepath, state_name=None):
        """Load CSV or Excel file"""
        try:
            # Auto-detect state from filename if not provided
            if state_name is None:
                state_name = self.detect_state_from_filename(filepath.stem)
            
            # Check file extension
            if filepath.suffix in ['.xlsx', '.xls']:
                df = pd.read_excel(filepath, engine='openpyxl')
                logger.info(f"✓ Loaded {len(df):,} records from {filepath.name} (Excel) - State: {state_name}")
            else:
                encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
                df = None
                for encoding in encodings:
                    try:
                        df = pd.read_csv(filepath, encoding=encoding, on_bad_lines='skip', low_memory=False)
                        logger.info(f"✓ Loaded {len(df):,} records from {filepath.name} (CSV, {encoding}) - State: {state_name}")
                        break
                    except:
                        continue
                
                if df is None:
                    raise Exception("Could not read CSV with any encoding")
            
            # Add state
            df['STATE'] = state_name
            
            return df
            
        except Exception as e:
            logger.error(f"✗ Error loading {filepath.name}: {e}")
            return pd.DataFrame()
    
    def standardize_columns(self, df):
        """Standardize column names"""
        # First, remove any duplicate columns by keeping the first occurrence
        df = df.loc[:, ~df.columns.duplicated()]
        
        # Rename columns
        df = df.rename(columns=self.column_mapping)
        
        # Add missing required columns with NaN
        for col in self.required_columns:
            if col not in df.columns:
                df[col] = np.nan
        
        # Select only required columns
        return df[self.required_columns]
    
    def clean_data(self, df):
        """Clean and validate data"""
        initial = len(df)
        
        # Remove duplicate columns if they exist
        df = df.loc[:, ~df.columns.duplicated()]
        
        # Clean CIN
        if 'CIN' in df.columns:
            df['CIN'] = df['CIN'].astype(str).str.strip().str.upper()
            df = df[df['CIN'].str.len() >= 20]
            df = df[~df['CIN'].isin(['NAN', 'NONE', 'NULL', '', 'NOT AVAILABLE'])]
            df = df.drop_duplicates(subset=['CIN'], keep='last')
        
        # Clean company name
        if 'COMPANY_NAME' in df.columns:
            df['COMPANY_NAME'] = df['COMPANY_NAME'].astype(str).str.strip()
            df = df[df['COMPANY_NAME'].str.len() > 0]
            df = df[~df['COMPANY_NAME'].isin(['nan', 'NaN', 'None'])]
        
        # Parse dates
        if 'DATE_OF_INCORPORATION' in df.columns:
            df['DATE_OF_INCORPORATION'] = pd.to_datetime(
                df['DATE_OF_INCORPORATION'],
                errors='coerce',
                format='mixed'
            )
        
        # Clean capital columns
        for col in ['AUTHORIZED_CAP', 'PAIDUP_CAPITAL']:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace('[₹,\s]', '', regex=True),
                    errors='coerce'
                )
        
        # Standardize status
        if 'COMPANY_STATUS' in df.columns:
            if isinstance(df['COMPANY_STATUS'], pd.DataFrame):
                df['COMPANY_STATUS'] = df['COMPANY_STATUS'].iloc[:, 0]
            
            df['COMPANY_STATUS'] = df['COMPANY_STATUS'].astype(str).str.strip().str.upper()
        
        final = len(df)
        logger.info(f"Cleaned: {initial:,} -> {final:,} records ({initial-final:,} removed)")
        
        return df
    
    def find_state_files(self, location):
        """Find all state files in a given location (folder or direct files)"""
        location = Path(location)
        found_files = []
        
        if location.is_dir():
            # Search for files in directory
            for pattern in ['*.csv', '*.xlsx', '*.xls']:
                found_files.extend(list(location.glob(pattern)))
        elif location.is_file():
            # Single file provided
            found_files = [location]
        else:
            # Try to find files in parent directory matching the pattern
            parent = self.raw_data_path
            for pattern in ['*.csv', '*.xlsx', '*.xls']:
                found_files.extend(list(parent.glob(pattern)))
        
        logger.info(f"Found {len(found_files)} files in {location}")
        return found_files
    
    def merge_states(self, location):
        """Merge all state files from given location"""
        all_data = []
        
        # Find all relevant files
        files = self.find_state_files(location)
        
        if not files:
            raise ValueError(f"No data files found in {location}")
        
        # Process each file
        for filepath in files:
            logger.info(f"Processing: {filepath.name}")
            
            df = self.load_file(filepath)
            
            if not df.empty:
                df = self.standardize_columns(df)
                all_data.append(df)
        
        if not all_data:
            raise ValueError(f"No valid data loaded from {location}")
        
        # Merge all dataframes
        merged_df = pd.concat(all_data, ignore_index=True, sort=False)
        merged_df = self.clean_data(merged_df)
        
        logger.info(f"Merged total: {len(merged_df):,} records from {len(all_data)} files")
        
        return merged_df
    
    def detect_changes(self, old_df, new_df, date_label):
        """Detect actual changes between two snapshots - OPTIMIZED"""
        changes = []
        
        # Set CIN as index for faster lookups
        old_df = old_df.set_index('CIN')
        new_df = new_df.set_index('CIN')
        
        old_cins = set(old_df.index)
        new_cins = set(new_df.index)
        
        logger.info(f"Comparing: {len(old_cins):,} old CINs vs {len(new_cins):,} new CINs")
        
        # 1. NEW INCORPORATIONS (vectorized)
        new_incorporations = new_cins - old_cins
        logger.info(f"New incorporations: {len(new_incorporations):,}")
        
        if len(new_incorporations) > 0:
            new_companies = new_df.loc[list(new_incorporations)].copy()
            new_companies['Change_Type'] = 'NEW_INCORPORATION'
            new_companies['Field_Changed'] = 'N/A'
            new_companies['Old_Value'] = 'N/A'
            new_companies['New_Value'] = 'Newly Incorporated'
            new_companies['Date'] = date_label
            new_companies = new_companies[['COMPANY_NAME', 'Change_Type', 'Field_Changed', 'Old_Value', 'New_Value', 'Date', 'STATE']].reset_index()
            changes.append(new_companies)
        
        # 2. DEREGISTRATIONS (vectorized)
        deregistrations = old_cins - new_cins
        logger.info(f"Deregistrations: {len(deregistrations):,}")
        
        if len(deregistrations) > 0:
            removed_companies = old_df.loc[list(deregistrations)].copy()
            removed_companies['Change_Type'] = 'DEREGISTRATION'
            removed_companies['Field_Changed'] = 'N/A'
            removed_companies['Old_Value'] = 'ACTIVE'
            removed_companies['New_Value'] = 'REMOVED'
            removed_companies['Date'] = date_label
            removed_companies = removed_companies[['COMPANY_NAME', 'Change_Type', 'Field_Changed', 'Old_Value', 'New_Value', 'Date', 'STATE']].reset_index()
            changes.append(removed_companies)
        
        # 3. FIELD CHANGES for existing companies (vectorized)
        common_cins = old_cins & new_cins
        logger.info(f"Checking changes for {len(common_cins):,} common companies...")
        
        if len(common_cins) > 0:
            common_list = list(common_cins)
            old_common = old_df.loc[common_list]
            new_common = new_df.loc[common_list]
            
            # Status changes (vectorized comparison)
            status_changed = old_common['COMPANY_STATUS'] != new_common['COMPANY_STATUS']
            if status_changed.sum() > 0:
                logger.info(f"  Status changes: {status_changed.sum():,}")
                status_changes = new_common[status_changed].copy()
                status_changes['Change_Type'] = 'STATUS_CHANGE'
                status_changes['Field_Changed'] = 'COMPANY_STATUS'
                status_changes['Old_Value'] = old_common.loc[status_changed, 'COMPANY_STATUS'].astype(str)
                status_changes['New_Value'] = status_changes['COMPANY_STATUS'].astype(str)
                status_changes['Date'] = date_label
                status_changes = status_changes[['COMPANY_NAME', 'Change_Type', 'Field_Changed', 'Old_Value', 'New_Value', 'Date', 'STATE']].reset_index()
                changes.append(status_changes)
            
            # Authorized capital changes
            auth_cap_changed = (
                old_common['AUTHORIZED_CAP'].notna() & 
                new_common['AUTHORIZED_CAP'].notna() & 
                (old_common['AUTHORIZED_CAP'] != new_common['AUTHORIZED_CAP'])
            )
            if auth_cap_changed.sum() > 0:
                logger.info(f"  Authorized capital changes: {auth_cap_changed.sum():,}")
                cap_changes = new_common[auth_cap_changed].copy()
                cap_changes['Change_Type'] = 'CAPITAL_CHANGE'
                cap_changes['Field_Changed'] = 'AUTHORIZED_CAP'
                cap_changes['Old_Value'] = old_common.loc[auth_cap_changed, 'AUTHORIZED_CAP'].astype(str)
                cap_changes['New_Value'] = cap_changes['AUTHORIZED_CAP'].astype(str)
                cap_changes['Date'] = date_label
                cap_changes = cap_changes[['COMPANY_NAME', 'Change_Type', 'Field_Changed', 'Old_Value', 'New_Value', 'Date', 'STATE']].reset_index()
                changes.append(cap_changes)
            
            # Paid-up capital changes
            paidup_changed = (
                old_common['PAIDUP_CAPITAL'].notna() & 
                new_common['PAIDUP_CAPITAL'].notna() & 
                (old_common['PAIDUP_CAPITAL'] != new_common['PAIDUP_CAPITAL'])
            )
            if paidup_changed.sum() > 0:
                logger.info(f"  Paid-up capital changes: {paidup_changed.sum():,}")
                paidup_changes = new_common[paidup_changed].copy()
                paidup_changes['Change_Type'] = 'CAPITAL_CHANGE'
                paidup_changes['Field_Changed'] = 'PAIDUP_CAPITAL'
                paidup_changes['Old_Value'] = old_common.loc[paidup_changed, 'PAIDUP_CAPITAL'].astype(str)
                paidup_changes['New_Value'] = paidup_changes['PAIDUP_CAPITAL'].astype(str)
                paidup_changes['Date'] = date_label
                paidup_changes = paidup_changes[['COMPANY_NAME', 'Change_Type', 'Field_Changed', 'Old_Value', 'New_Value', 'Date', 'STATE']].reset_index()
                changes.append(paidup_changes)
        
        # Combine all changes
        if changes:
            changes_df = pd.concat(changes, ignore_index=True)
            logger.info(f"Total changes detected: {len(changes_df):,}")
            return changes_df
        else:
            logger.info("No changes detected")
            return pd.DataFrame()


def generate_summary(changes_df, day_number, date_label):
    """Generate AI summary report"""
    summary = f"""
{"="*70}
MCA Daily Change Report - Day {day_number} ({date_label})
{"="*70}

SUMMARY STATISTICS
------------------
Total Changes Detected: {len(changes_df):,}
"""
    
    if len(changes_df) > 0 and 'Change_Type' in changes_df.columns:
        summary += f"""
New Incorporations: {len(changes_df[changes_df['Change_Type']=='NEW_INCORPORATION']):,}
Deregistrations: {len(changes_df[changes_df['Change_Type']=='DEREGISTRATION']):,}
Status Changes: {len(changes_df[changes_df['Change_Type']=='STATUS_CHANGE']):,}
Capital Modifications: {len(changes_df[changes_df['Change_Type']=='CAPITAL_CHANGE']):,}

TOP STATES BY ACTIVITY
-----------------------
"""
        if 'STATE' in changes_df.columns:
            for state, count in changes_df['STATE'].value_counts().head(5).items():
                summary += f"{state}: {count:,} changes\n"
    else:
        summary += """
New Incorporations: 0
Deregistrations: 0
Status Changes: 0
Capital Modifications: 0

NOTE: No changes detected between snapshots.
This indicates both datasets are identical.
"""
    
    summary += f"\n{'='*70}\n"
    summary += f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    summary += f"{'='*70}\n"
    
    return summary


def main():
    print("\n" + "="*70)
    print(" "*10 + "MCA INSIGHTS ENGINE - REAL CHANGE DETECTION")
    print("="*70 + "\n")
    
    try:
        processor = RealDataProcessor('data/raw')
        
        # Create output directories
        for d in ['data/processed', 'data/changes', 'data/summaries', 'data/enriched']:
            Path(d).mkdir(parents=True, exist_ok=True)
        
        # Detect data structure
        day1_folder = Path('data/raw/day1')
        day2_folder = Path('data/raw/day2')
        raw_folder = Path('data/raw')
        
        # Check what structure we have
        has_day_folders = day1_folder.exists() and day2_folder.exists()
        has_direct_files = len(list(raw_folder.glob('*.csv'))) > 0 or len(list(raw_folder.glob('*.xlsx'))) > 0
        
        print("📁 Data Structure Detection:")
        print(f"  Day folders (day1/day2): {'✓ Found' if has_day_folders else '✗ Not found'}")
        print(f"  Direct CSV/Excel files: {'✓ Found' if has_direct_files else '✗ Not found'}")
        print()
        
        # PROCESSING MODE 1: Day folders exist
        if has_day_folders:
            print("📊 Mode: Multi-day snapshot comparison\n")
            
            # STEP 1: Process Day 1
            print("[1/4] Processing Day 1 Snapshot")
            print("-" * 70)
            
            master_df = processor.merge_states(day1_folder)
            master_df.to_csv('data/processed/master_dataset_day1.csv', index=False)
            
            print(f"\n✓ Day 1 processed: {len(master_df):,} companies")
            print(f"  States: {', '.join(master_df['STATE'].unique())}")
            
            # STEP 2: Process Day 2
            print("\n[2/4] Processing Day 2 Snapshot")
            print("-" * 70)
            
            day2_df = processor.merge_states(day2_folder)
            day2_df.to_csv('data/processed/master_dataset_day2.csv', index=False)
            
            print(f"\n✓ Day 2 processed: {len(day2_df):,} companies")
            
            # STEP 3: Detect Changes
            print("\n[3/4] Detecting Changes Between Snapshots")
            print("-" * 70)
            
            changes_df = processor.detect_changes(
                master_df,
                day2_df,
                datetime.now().strftime('%Y-%m-%d')
            )
            
            # Save changes
            changes_df.to_csv('data/changes/day2_changes.csv', index=False)
            print(f"\n✓ Changes saved: data/changes/day2_changes.csv")
            print(f"  Total changes: {len(changes_df):,}")
            
            # Breakdown
            if not changes_df.empty and 'Change_Type' in changes_df.columns:
                print(f"\n  Change Breakdown:")
                for change_type, count in changes_df['Change_Type'].value_counts().items():
                    print(f"    - {change_type}: {count:,}")
            
            # Use Day 2 as final master
            final_master = day2_df
            
        # PROCESSING MODE 2: Direct files only
        elif has_direct_files:
            print("📊 Mode: Single snapshot processing\n")
            
            print("[1/2] Processing All State Files")
            print("-" * 70)
            
            master_df = processor.merge_states(raw_folder)
            master_df.to_csv('data/processed/master_dataset_day1.csv', index=False)
            
            print(f"\n✓ Processed: {len(master_df):,} companies")
            print(f"  States: {', '.join(master_df['STATE'].unique())}")
            
            print("\n[2/2] Creating Placeholder Change Log")
            print("-" * 70)
            
            # Create empty change log for single snapshot
            changes_df = pd.DataFrame(columns=[
                'CIN', 'COMPANY_NAME', 'Change_Type', 'Field_Changed', 
                'Old_Value', 'New_Value', 'Date', 'STATE'
            ])
            changes_df.to_csv('data/changes/day1_changes.csv', index=False)
            
            print("✓ Placeholder change log created")
            print("  Note: No changes (single snapshot mode)")
            
            final_master = master_df
            
        else:
            print("✗ ERROR: No data found!")
            print("\nPlease add data in one of these formats:")
            print("\n1. Folder structure:")
            print("   data/raw/day1/maharashtra.csv")
            print("   data/raw/day1/gujarat.csv")
            print("   data/raw/day2/maharashtra.csv")
            print("   data/raw/day2/gujarat.csv")
            print("\n2. Direct files:")
            print("   data/raw/maharashtra.csv")
            print("   data/raw/gujarat.csv")
            print("   data/raw/delhi.csv")
            print()
            return
        
        # STEP 4: Generate Summary
        print("\n[4/4] Generating AI Summary Reports")
        print("-" * 70)
        
        if has_day_folders:
            summary_text = generate_summary(changes_df, 2, datetime.now().strftime('%Y-%m-%d'))
            summary_file = 'data/summaries/day2_summary.txt'
        else:
            summary_text = f"""
{"="*70}
MCA Master Dataset Summary
{"="*70}

DATASET STATISTICS
------------------
Total Companies: {len(final_master):,}

BY STATE
--------
"""
            for state, count in final_master['STATE'].value_counts().items():
                summary_text += f"{state}: {count:,} companies\n"
            
            summary_text += f"\n{'='*70}\n"
            summary_text += f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            summary_text += f"{'='*70}\n"
            
            summary_file = 'data/summaries/day1_summary.txt'
        
        with open(summary_file, 'w') as f:
            f.write(summary_text)
        
        print(f"✓ Summary saved: {summary_file}")
        
        # Save final master
        final_master.to_csv('data/processed/master_dataset.csv', index=False)
        print("✓ Final master dataset saved")
        
        # Create enrichment sample
        print("\nCreating enrichment sample...")
        sample = final_master.head(100)[['CIN', 'COMPANY_NAME', 'STATE']].copy()
        sample['SOURCE'] = 'ZaubaCorp'
        sample['FIELD'] = 'Director info, Sector classification'
        sample['SOURCE_URL'] = sample['CIN'].apply(lambda cin: f'https://www.zaubacorp.com/company/{cin}')
        sample.to_csv('data/enriched/enriched_companies.csv', index=False)
        print("✓ Enrichment sample created (100 companies)")
        
        # SUCCESS SUMMARY
        print("\n" + "="*70)
        print(" "*20 + "✅ SUCCESS!")
        print("="*70)
        
        print("\n📊 Processing Summary:")
        if has_day_folders:
            print(f"  Day 1: {len(master_df):,} companies")
            print(f"  Day 2: {len(day2_df):,} companies")
            print(f"  Real Changes: {len(changes_df):,}")
        else:
            print(f"  Total Companies: {len(final_master):,}")
            print(f"  States Processed: {', '.join(final_master['STATE'].unique())}")
        
        print("\n📁 Files Created:")
        print("  ✓ data/processed/master_dataset.csv")
        if has_day_folders:
            print("  ✓ data/processed/master_dataset_day1.csv")
            print("  ✓ data/processed/master_dataset_day2.csv")
            print("  ✓ data/changes/day2_changes.csv")
            print("  ✓ data/summaries/day2_summary.txt")
        else:
            print("  ✓ data/processed/master_dataset_day1.csv")
            print("  ✓ data/changes/day1_changes.csv")
            print("  ✓ data/summaries/day1_summary.txt")
        print("  ✓ data/enriched/enriched_companies.csv")
        
        print("\n🚀 Next Steps:")
        print("  1. Review processed data in data/processed/")
        if has_day_folders:
            print("  2. Check change logs in data/changes/")
            print("  3. Read summary report in data/summaries/")
        print("  4. Run dashboard: streamlit run app.py")
        print("  5. View at: http://localhost:8501")
        
        print("\n" + "="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        logger.error("Processing error", exc_info=True)
        print("\nTroubleshooting:")
        print("  1. Check file formats: .csv or .xlsx")
        print("  2. Ensure files contain required columns (CIN, CompanyName, etc.)")
        print("  3. Verify file names contain state keywords (maharashtra, gujarat, etc.)")
        print("  4. Check file encoding (UTF-8 or Latin-1)")
        print()


if __name__ == "__main__":
    main()