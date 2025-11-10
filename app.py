import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import json
from datetime import datetime, timedelta
import time
from groq import Groq
import io
import urllib.parse
import random

# Page configuration
st.set_page_config(
    page_title="🚀 SME Digital Transformation Scout",
    page_icon="🤖",
    layout="wide"
)

class SMEDigitalTransformationScout:
    def __init__(self):
        self.groq_client = Groq(api_key=st.secrets.get("GROQ_API_KEY"))
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Target industries for SMEs
        self.INDUSTRIES = [
            "Manufacturing", "BFSI", "Healthcare", "Hospitals", 
            "Pharmaceutical", "Insurance", "Banking", "Financial Services",
            "Logistics", "Retail", "Education", "Real Estate", "Construction"
        ]
        
        # Digital transformation technologies for SMEs
        self.DIGITAL_TECHNOLOGIES = [
            "DMS", "Document Management System", "DCM", "Digital Contract Management",
            "ERP", "Enterprise Resource Planning", "RPA", "Robotic Process Automation",
            "Managed IT Services", "AI", "Artificial Intelligence", "Data Analytics",
            "digital transformation", "cloud migration", "automation", "business intelligence",
            "SAP Business One", "Zoho", "Tally", "QuickBooks", "Microsoft 365"
        ]
        
        # SME indicators and revenue ranges
        self.SME_INDICATORS = [
            "SME", "small and medium", "startup", "MSME", "small business",
            "growing company", "emerging company", "mid-sized", "family business",
            "entrepreneur", "revenue under", "turnover under", "crore company"
        ]
        
        # SME revenue ranges (in INR Crores)
        self.SME_REVENUE_RANGES = [
            "1-10 crore", "10-50 crore", "50-100 crore", "100-250 crore",
            "Under 1 crore", "1-5 crore", "5-25 crore", "25-100 crore"
        ]
        
        # Indian states to exclude (Kerala)
        self.EXCLUDE_STATES = ["Kerala", "kerala"]

    def search_google_news_rss(self, query, max_results=20):
        """Free Google News RSS search for SME digital transformation news"""
        try:
            base_url = "https://news.google.com/rss"
            
            # Enhanced query with SME focus
            enhanced_query = f"{query} India -Kerala (SME OR startup OR 'small business') after:2024-01-01"
            
            search_url = f"{base_url}/search?q={enhanced_query.replace(' ', '%20')}&hl=en-IN&gl=IN&ceid=IN:en"
            
            response = self.session.get(search_url, timeout=15)
            if response.status_code == 200:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.content)
                
                articles = []
                for item in root.findall('.//item')[:max_results]:
                    title = item.find('title').text if item.find('title') is not None else ''
                    link = item.find('link').text if item.find('link') is not None else ''
                    pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
                    description = item.find('description').text if item.find('description') is not None else ''
                    
                    # Clean HTML tags from description
                    description = re.sub(r'<[^>]+>', '', description)
                    
                    # Skip if mentions Kerala
                    if any(state in (title + description).lower() for state in [s.lower() for s in self.EXCLUDE_STATES]):
                        continue
                    
                    articles.append({
                        'title': title,
                        'link': link,
                        'description': description,
                        'source': 'Google News',
                        'date': pub_date,
                        'content': f"{title}. {description}"
                    })
                
                return articles
            return []
        except Exception as e:
            st.error(f"Google News error: {str(e)}")
            return []

    def build_sme_search_queries(self, selected_industries, technologies):
        """Build targeted queries for SME digital transformation"""
        base_queries = []
        
        # SME-specific digital transformation queries
        sme_terms = ["SME", "small business", "startup", "MSME", "growing company", "mid-sized"]
        
        for industry in selected_industries:
            for sme_term in sme_terms[:3]:  # Use top 3 SME terms
                industry_queries = [
                    f"{industry} {sme_term} digital transformation India",
                    f"{industry} {sme_term} ERP implementation India",
                    f"{industry} {sme_term} cloud migration India",
                    f"{industry} {sme_term} automation India",
                    f"{sme_term} {industry} company technology upgrade India"
                ]
                base_queries.extend(industry_queries)
        
        # Technology-specific queries for SMEs
        for tech in technologies[:5]:
            for sme_term in sme_terms[:2]:
                tech_queries = [
                    f"{sme_term} {tech} implementation India",
                    f"{sme_term} {tech} adoption India",
                    f"{tech} for small business India"
                ]
                base_queries.extend(tech_queries)
        
        # Funding and growth news (indicators of digital transformation)
        funding_terms = ["funding", "investment", "series A", "series B", "growth funding"]
        for industry in selected_industries[:2]:
            for term in funding_terms:
                base_queries.append(f"{industry} {term} India digital transformation")
        
        return list(set(base_queries))[:20]  # Limit to 20 unique queries

    def hybrid_search(self, search_terms, max_results_per_source=15):
        """Hybrid search across multiple free sources"""
        all_articles = []
        
        for term in search_terms:
            st.info(f"🔍 Searching: {term}")
            
            # Google News search
            google_articles = self.search_google_news_rss(term, max_results_per_source)
            all_articles.extend(google_articles)
            time.sleep(1)
            
            # DuckDuckGo search for broader coverage
            try:
                base_url = "https://html.duckduckgo.com/html/"
                params = {'q': term, 'kl': 'in-en'}
                
                response = self.session.post(base_url, data=params, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    results = soup.find_all('div', class_='result')
                    
                    for result in results[:max_results_per_source]:
                        try:
                            title_elem = result.find('a', class_='result__a')
                            snippet_elem = result.find('a', class_='result__snippet')
                            
                            if title_elem:
                                title = title_elem.text.strip()
                                link = title_elem.get('href')
                                snippet = snippet_elem.text.strip() if snippet_elem else ""
                                
                                # Skip if mentions Kerala
                                if any(state in (title + snippet).lower() for state in [s.lower() for s in self.EXCLUDE_STATES]):
                                    continue
                                
                                # Extract actual URL from DuckDuckGo redirect
                                if link and 'uddg=' in link:
                                    match = re.search(r'uddg=([^&]+)', link)
                                    if match:
                                        link = urllib.parse.unquote(match.group(1))
                                
                                if link and any(domain in link for domain in ['.com', '.in', '.org', '.net', '.co']):
                                    all_articles.append({
                                        'title': title,
                                        'link': link,
                                        'description': snippet,
                                        'source': 'DuckDuckGo',
                                        'date': '2024+',
                                        'content': f"{title}. {snippet}"
                                    })
                        except Exception:
                            continue
            except Exception as e:
                st.warning(f"DuckDuckGo search error: {str(e)}")
            
            time.sleep(1)
        
        # Remove duplicates based on URL and title
        seen_articles = set()
        unique_articles = []
        for article in all_articles:
            article_key = f"{article['title'][:100]}_{article['link']}"
            if article_key not in seen_articles:
                seen_articles.add(article_key)
                unique_articles.append(article)
        
        return unique_articles

    def analyze_company_size(self, company_data):
        """Analyze and determine company size based on available data"""
        revenue = company_data.get('Revenue', '').lower()
        company_name = company_data.get('Company Name', '').lower()
        content = company_data.get('Transformation Details', '').lower()
        
        # SME indicators
        sme_score = 0
        revenue_range = "Not specified"
        
        # Check for SME indicators in content
        for indicator in self.SME_INDICATORS:
            if indicator in content or indicator in company_name:
                sme_score += 1
        
        # Analyze revenue mentions
        revenue_patterns = {
            "1-10 crore": r'(\d+\s*-\s*\d+\s*crore|₹?\s*\d+\s*crore)',
            "10-50 crore": r'(\d+\s*-\s*\d+\s*crore|₹?\s*\d+\s*crore)',
            "Under 1 crore": r'under\s*\d+\s*crore|less than\s*\d+\s*crore',
        }
        
        for range_name, pattern in revenue_patterns.items():
            if re.search(pattern, revenue, re.IGNORECASE):
                revenue_range = range_name
                sme_score += 2
                break
        
        # Determine company size category
        if sme_score >= 3:
            company_size = "SME (Small to Medium Enterprise)"
        elif sme_score >= 1:
            company_size = "Likely SME"
        else:
            company_size = "Size Unknown"
        
        return company_size, revenue_range, sme_score

    def extract_company_data_with_groq(self, articles, batch_size=25, delay_between_batches=2):
        """Use Groq to extract SME digital transformation company data with batch processing"""
        if not articles:
            return []
            
        extracted_data = []
        total_batches = (len(articles) + batch_size - 1) // batch_size
        
        st.info(f"📊 Processing {len(articles)} articles in {total_batches} batches of {batch_size}")
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min((batch_num + 1) * batch_size, len(articles))
            batch_articles = articles[start_idx:end_idx]
            
            st.write(f"**Processing batch {batch_num + 1}/{total_batches} (articles {start_idx + 1}-{end_idx})**")
            
            batch_data = self._process_batch(batch_articles, batch_num + 1, total_batches)
            extracted_data.extend(batch_data)
            
            # Add delay between batches to avoid rate limits
            if batch_num < total_batches - 1:
                st.info(f"⏳ Waiting {delay_between_batches} seconds before next batch...")
                time.sleep(delay_between_batches)
        
        return extracted_data

    def _process_batch(self, batch_articles, batch_num, total_batches):
        """Process a single batch of articles"""
        batch_data = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Enhanced system prompt for SME digital transformation
        system_prompt = f"""You are an expert Indian business analyst specializing in SME digital transformation. Extract company information from news articles with focus on small to medium enterprises.

TARGET INDUSTRIES: {', '.join(self.INDUSTRIES)}
DIGITAL TECHNOLOGIES: {', '.join(self.DIGITAL_TECHNOLOGIES)}
SME INDICATORS: {', '.join(self.SME_INDICATORS)}
EXCLUDE: Kerala-based companies, Large enterprises (revenue > 1000 crore)

CRITICAL: Focus on SMALL TO MEDIUM ENTERPRISES (SMEs). Look for:
- Revenue under 250 crore
- Growing companies, startups, family businesses
- Digital transformation initiatives for SMEs
- ERP, DMS, DCM, RPA implementations in SMEs
- AI and Data Analytics adoption by small businesses

Return EXACT JSON format:
{{
    "companies": [
        {{
            "company_name": "extracted company name",
            "website": "company website if mentioned, else empty",
            "industry": "Manufacturing/BFSI/Healthcare/Hospitals/Logistics/Retail",
            "revenue": "revenue information if mentioned, else 'Not specified'",
            "revenue_range": "1-10 crore/10-50 crore/50-100 crore/100-250 crore/Not specified",
            "employee_count": "employee count if mentioned, else 'Not specified'",
            "digital_transformation": "Yes/No",
            "transformation_details": "specific technologies and projects mentioned",
            "hiring_trends_2025_2026": "hiring indications if mentioned, else 'Not specified'",
            "company_size_indication": "SME/Startup/Growing Business/Large Enterprise/Unknown",
            "growth_stage": "Early-stage/ Growth-stage/ Mature SME/ Unknown",
            "confidence_score": "high/medium/low"
        }}
    ]
}}

If no SME companies found, return: {{"companies": []}}"""
        
        processed_count = 0
        for i, article in enumerate(batch_articles):
            try:
                status_text.text(f"🤖 Batch {batch_num}/{total_batches} - Analyzing article {i+1}/{len(batch_articles)}...")
                progress_bar.progress((i + 1) / len(batch_articles))
                
                content = article['content']
                if len(content) > 3000:
                    content = content[:3000]
                
                user_prompt = f"""
                Analyze this Indian business/technology news article for SME companies undergoing digital transformation:

                TITLE: {article['title']}
                CONTENT: {content}

                Extract ALL SME companies mentioned. Focus on:
                - Industries: {', '.join(self.INDUSTRIES)}
                - Technologies: {', '.join(self.DIGITAL_TECHNOLOGIES)}
                - SME Indicators: {', '.join(self.SME_INDICATORS)}
                - Exclude companies based in Kerala
                - Look for revenue mentions (prefer under 250 crore)
                - Look for hiring trends for 2025-2026
                - Focus on small to medium enterprises, not large corporations
                """
                
                # Use chat completion with retry logic
                max_retries = 2
                for attempt in range(max_retries):
                    try:
                        chat_completion = self.groq_client.chat.completions.create(
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            model="llama-3.3-70b-versatile",
                            temperature=0.1,
                            max_tokens=2500,
                            response_format={"type": "json_object"}
                        )
                        
                        response_text = chat_completion.choices[0].message.content
                        break
                        
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise e
                        time.sleep(1)
                
                # Parse and validate response
                try:
                    data = json.loads(response_text.strip())
                    companies = data.get('companies', [])
                    
                    for company in companies:
                        # Validate required fields and SME focus
                        if (company.get('company_name') and 
                            company.get('company_name') != 'null' and
                            company.get('digital_transformation') == 'Yes' and
                            company.get('company_size_indication') in ['SME', 'Startup', 'Growing Business']):
                            
                            # Enhanced company data with SME analysis
                            company_size, revenue_range, sme_score = self.analyze_company_size(company)
                            
                            batch_data.append({
                                'Company Name': company['company_name'],
                                'Website': company.get('website', 'Not specified'),
                                'Industry': company.get('industry', 'Not specified'),
                                'Revenue': company.get('revenue', 'Not specified'),
                                'Revenue Range': company.get('revenue_range', 'Not specified'),
                                'Employee Count': company.get('employee_count', 'Not specified'),
                                'Digital Transformation': company.get('digital_transformation', 'No'),
                                'Transformation Details': company.get('transformation_details', 'Digital initiatives mentioned'),
                                'Hiring Trends 2025-2026': company.get('hiring_trends_2025_2026', 'Not specified'),
                                'Company Size': company_size,
                                'Growth Stage': company.get('growth_stage', 'Unknown'),
                                'SME Score': sme_score,
                                'Source Link': article['link'],
                                'Article Title': article['title'],
                                'Source': article['source'],
                                'Date': article.get('date', '2024+'),
                                'Confidence': company.get('confidence_score', 'medium')
                            })
                            processed_count += 1
                            
                except json.JSONDecodeError as e:
                    st.warning(f"Failed to parse JSON from article {i+1}: {str(e)}")
                    continue
                    
            except Exception as e:
                st.warning(f"Error processing article {i+1}: {str(e)}")
                continue
        
        progress_bar.empty()
        status_text.empty()
        
        if processed_count > 0:
            st.success(f"✅ Batch {batch_num}: Processed {processed_count} SME companies")
        else:
            st.warning(f"⚠️ Batch {batch_num}: No SME companies found in this batch")
        
        return batch_data

    def calculate_sme_relevance_score(self, company):
        """Calculate relevance score specifically for SME digital transformation"""
        score = 0
        
        # Confidence scoring
        if company['Confidence'] == 'high':
            score += 3
        elif company['Confidence'] == 'medium':
            score += 2
        else:
            score += 1
        
        # SME scoring
        sme_size = company['Company Size'].lower()
        if 'sme' in sme_size or 'small' in sme_size or 'startup' in sme_size:
            score += 3
        elif 'growing' in sme_size:
            score += 2
        
        # SME score from analysis
        score += min(company.get('SME Score', 0), 3)
        
        # Technology depth
        tech_keywords = ['ERP', 'AI', 'DMS', 'RPA', 'analytics', 'cloud', 'automation']
        details = company['Transformation Details'].lower()
        tech_count = sum(1 for tech in tech_keywords if tech.lower() in details)
        score += min(tech_count, 3)
        
        # Hiring trends bonus
        hiring = company['Hiring Trends 2025-2026'].lower()
        if 'active' in hiring or 'hiring' in hiring or 'expanding' in hiring:
            score += 2
        
        # Revenue range scoring (prefer smaller SMEs)
        revenue_range = company.get('Revenue Range', '').lower()
        if '1-10' in revenue_range or 'under' in revenue_range:
            score += 2
        elif '10-50' in revenue_range:
            score += 1
        
        return min(score, 10)  # Cap at 10

    def filter_and_rank_sme_companies(self, companies):
        """Filter and rank companies by SME relevance"""
        if not companies:
            return []
        
        # Sort by relevance score
        companies.sort(key=lambda x: x['Relevance Score'], reverse=True)
        
        # Remove duplicates based on company name
        seen_companies = set()
        unique_companies = []
        for company in companies:
            company_key = company['Company Name'].lower().strip()
            if company_key not in seen_companies:
                seen_companies.add(company_key)
                unique_companies.append(company)
        
        return unique_companies

    def generate_enhanced_output(self, companies):
        """Generate enhanced output with all SME fields"""
        if not companies:
            return "No SME digital transformation companies found"
        
        output_lines = ["Company Name\tWebsite\tIndustry\tRevenue\tRevenue Range\tEmployee Count\tDigital Transformation\tTransformation Details\tHiring Trends 2025-2026\tCompany Size\tGrowth Stage\tConfidence\tRelevance Score\tSource Link"]
        
        for company in companies:
            company_name = str(company['Company Name']).replace('\t', ' ').replace('\n', ' ')
            website = str(company['Website']).replace('\t', ' ')
            industry = str(company['Industry']).replace('\t', ' ')
            revenue = str(company['Revenue']).replace('\t', ' ')
            revenue_range = str(company['Revenue Range']).replace('\t', ' ')
            employee_count = str(company['Employee Count']).replace('\t', ' ')
            digital_transformation = str(company['Digital Transformation']).replace('\t', ' ')
            transformation_details = str(company['Transformation Details']).replace('\t', ' ').replace('\n', ' ')
            hiring_trends = str(company['Hiring Trends 2025-2026']).replace('\t', ' ')
            company_size = str(company['Company Size']).replace('\t', ' ')
            growth_stage = str(company['Growth Stage']).replace('\t', ' ')
            confidence = str(company['Confidence']).replace('\t', ' ')
            relevance_score = str(company['Relevance Score'])
            source_link = str(company['Source Link']).replace('\t', ' ')
            
            output_line = f"{company_name}\t{website}\t{industry}\t{revenue}\t{revenue_range}\t{employee_count}\t{digital_transformation}\t{transformation_details}\t{hiring_trends}\t{company_size}\t{growth_stage}\t{confidence}\t{relevance_score}\t{source_link}"
            output_lines.append(output_line)
        
        return "\n".join(output_lines)

    def display_sme_insights(self, companies):
        """Display insights about SME digital transformation trends"""
        if not companies:
            return
        
        st.header("📊 SME Digital Transformation Insights")
        
        # Create columns for different insights
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Company Size Distribution")
            sizes = [company['Company Size'] for company in companies]
            size_df = pd.DataFrame({'Company Size': sizes})
            size_counts = size_df['Company Size'].value_counts()
            if not size_counts.empty:
                st.bar_chart(size_counts)
            else:
                st.info("No size data available")
        
        with col2:
            st.subheader("Technology Adoption")
            tech_keywords = ['ERP', 'AI', 'Cloud', 'RPA', 'Analytics', 'DMS', 'Automation']
            tech_counts = {}
            for company in companies:
                details = company['Transformation Details'].lower()
                for tech in tech_keywords:
                    if tech.lower() in details:
                        tech_counts[tech] = tech_counts.get(tech, 0) + 1
            
            if tech_counts:
                tech_df = pd.DataFrame(list(tech_counts.items()), columns=['Technology', 'Count'])
                st.bar_chart(tech_df.set_index('Technology'))
            else:
                st.info("No technology data available")
        
        with col3:
            st.subheader("Hiring Trends 2025-2026")
            hiring_companies = len([c for c in companies if 'hiring' in c['Hiring Trends 2025-2026'].lower() or 'active' in c['Hiring Trends 2025-2026'].lower()])
            total_companies = len(companies)
            
            if total_companies > 0:
                hiring_percentage = (hiring_companies / total_companies) * 100
                st.metric("SMEs Hiring (2025-2026)", f"{hiring_percentage:.1f}%")
                st.metric("Total SMEs Analyzed", total_companies)
            else:
                st.metric("SMEs Hiring", "0%")

class JobPlatformScout:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Job platforms to search
        self.JOB_PLATFORMS = {
            "LinkedIn": ["linkedin.com/jobs", "linkedin.com/company"],
            "Naukri": ["naukri.com", "naukrihub.com"],
            "Indeed": ["indeed.com", "indeed.co.in"],
            "Glassdoor": ["glassdoor.com", "glassdoor.co.in"],
            "Monster": ["monster.com", "monsterindia.com"],
            "TimesJobs": ["timesjobs.com"],
            "Shine": ["shine.com"]
        }
        
        # Job roles related to digital transformation
        self.DIGITAL_TRANSFORMATION_ROLES = [
            "ERP", "DMS", "DCM", "RPA", "AI", "Data Analytics", "Digital Transformation",
            "IT Manager", "CTO", "Technology Head", "Digital Manager",
            "Business Analyst", "Systems Analyst", "IT Project Manager"
        ]

    def search_jobs_by_company(self, company_names, max_results_per_company=10):
        """Search job platforms for specific companies"""
        all_job_listings = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, company_name in enumerate(company_names):
            status_text.text(f"🔍 Searching jobs for: {company_name}")
            progress_bar.progress((i + 1) / len(company_names))
            
            company_jobs = self._search_company_jobs(company_name, max_results_per_company)
            all_job_listings.extend(company_jobs)
            
            time.sleep(1)  # Be respectful to search engines
        
        progress_bar.empty()
        status_text.empty()
        
        return all_job_listings

    def _search_company_jobs(self, company_name, max_results):
        """Search for jobs for a specific company"""
        jobs_found = []
        
        # Build search queries
        queries = [
            f'"{company_name}" hiring India',
            f'"{company_name}" careers India',
            f'"{company_name}" jobs India',
            f'"{company_name}" recruitment India'
        ]
        
        for query in queries[:2]:  # Use first 2 queries
            try:
                # Use DuckDuckGo to search job platforms
                base_url = "https://html.duckduckgo.com/html/"
                platform_sites = " OR ".join([f"site:{domain}" for platforms in self.JOB_PLATFORMS.values() for domain in platforms])
                params = {
                    'q': f"{query} ({platform_sites})",
                    'kl': 'in-en',
                }
                
                response = self.session.post(base_url, data=params, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    results = soup.find_all('div', class_='result')
                    
                    for result in results[:max_results]:
                        try:
                            title_elem = result.find('a', class_='result__a')
                            snippet_elem = result.find('a', class_='result__snippet')
                            
                            if title_elem:
                                title = title_elem.text.strip()
                                link = title_elem.get('href')
                                snippet = snippet_elem.text.strip() if snippet_elem else ""
                                
                                # Extract actual URL from DuckDuckGo redirect
                                if link and 'uddg=' in link:
                                    match = re.search(r'uddg=([^&]+)', link)
                                    if match:
                                        link = urllib.parse.unquote(match.group(1))
                                
                                # Identify job platform
                                platform = "Other"
                                for platform_name, domains in self.JOB_PLATFORMS.items():
                                    if any(domain in link for domain in domains):
                                        platform = platform_name
                                        break
                                
                                # Check if it's a digital transformation role
                                role_type = "General"
                                for role in self.DIGITAL_TRANSFORMATION_ROLES:
                                    if role.lower() in title.lower() or role.lower() in snippet.lower():
                                        role_type = "Digital Transformation"
                                        break
                                
                                jobs_found.append({
                                    'Company': company_name,
                                    'Job Title': title,
                                    'Platform': platform,
                                    'Link': link,
                                    'Description': snippet,
                                    'Role Type': role_type,
                                    'Date Found': datetime.now().strftime('%Y-%m-%d')
                                })
                        except Exception:
                            continue
                
                time.sleep(1)  # Be respectful to the search engine
                
            except Exception as e:
                st.warning(f"Job search error for {company_name}: {str(e)}")
                continue
        
        return jobs_found

    def search_jobs_by_technology(self, technologies, locations=None, max_results=20):
        """Search for jobs by specific technologies"""
        if locations is None:
            locations = ["India", "Bangalore", "Hyderabad", "Pune", "Chennai"]
        
        all_tech_jobs = []
        
        for tech in technologies[:3]:  # Search for top 3 technologies
            for location in locations[:2]:  # Search in top 2 locations
                try:
                    query = f"{tech} jobs {location}"
                    
                    base_url = "https://html.duckduckgo.com/html/"
                    platform_sites = " OR ".join([f"site:{domain}" for platforms in self.JOB_PLATFORMS.values() for domain in platforms])
                    params = {
                        'q': f"{query} ({platform_sites})",
                        'kl': 'in-en',
                    }
                    
                    response = self.session.post(base_url, data=params, timeout=15)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        results = soup.find_all('div', class_='result')
                        
                        for result in results[:max_results]:
                            try:
                                title_elem = result.find('a', class_='result__a')
                                snippet_elem = result.find('a', class_='result__snippet')
                                
                                if title_elem:
                                    title = title_elem.text.strip()
                                    link = title_elem.get('href')
                                    snippet = snippet_elem.text.strip() if snippet_elem else ""
                                    
                                    # Extract company name from title/snippet
                                    company_name = self._extract_company_name(title, snippet)
                                    
                                    # Extract actual URL
                                    if link and 'uddg=' in link:
                                        match = re.search(r'uddg=([^&]+)', link)
                                        if match:
                                            link = urllib.parse.unquote(match.group(1))
                                    
                                    # Identify platform
                                    platform = "Other"
                                    for platform_name, domains in self.JOB_PLATFORMS.items():
                                        if any(domain in link for domain in domains):
                                            platform = platform_name
                                            break
                                    
                                    all_tech_jobs.append({
                                        'Company': company_name,
                                        'Job Title': title,
                                        'Technology': tech,
                                        'Location': location,
                                        'Platform': platform,
                                        'Link': link,
                                        'Description': snippet,
                                        'Date Found': datetime.now().strftime('%Y-%m-%d')
                                    })
                            except Exception:
                                continue
                    
                    time.sleep(1)
                    
                except Exception as e:
                    st.warning(f"Technology job search error for {tech}: {str(e)}")
                    continue
        
        return all_tech_jobs

    def _extract_company_name(self, title, snippet):
        """Extract company name from job title and description"""
        # Common patterns in job titles
        patterns = [
            r'at\s+([A-Za-z0-9\s&]+)',
            r'-\s*([A-Za-z0-9\s&]+)\s* hiring',
            r'([A-Za-z0-9\s&]+)\s*is hiring',
            r'jobs? at\s+([A-Za-z0-9\s&]+)'
        ]
        
        text = f"{title} {snippet}"
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Unknown Company"

    def generate_jobs_output(self, job_listings):
        """Generate TSV output for job listings"""
        if not job_listings:
            return "No job listings found"
        
        output_lines = ["Company\tJob Title\tPlatform\tRole Type\tTechnology\tLocation\tLink\tDate Found"]
        
        for job in job_listings:
            company = str(job.get('Company', '')).replace('\t', ' ')
            job_title = str(job.get('Job Title', '')).replace('\t', ' ')
            platform = str(job.get('Platform', '')).replace('\t', ' ')
            role_type = str(job.get('Role Type', 'General')).replace('\t', ' ')
            technology = str(job.get('Technology', '')).replace('\t', ' ')
            location = str(job.get('Location', '')).replace('\t', ' ')
            link = str(job.get('Link', '')).replace('\t', ' ')
            date_found = str(job.get('Date Found', ''))
            
            output_line = f"{company}\t{job_title}\t{platform}\t{role_type}\t{technology}\t{location}\t{link}\t{date_found}"
            output_lines.append(output_line)
        
        return "\n".join(output_lines)

def main():
    st.title("🚀 SME Digital Transformation Scout")
    st.markdown("""
    **Discover Small-to-Medium Indian companies undergoing digital transformation**  
    *Targeting Manufacturing, BFSI, Healthcare & Hospitals (Excluding Kerala)*
    """)
    
    if not st.secrets.get("GROQ_API_KEY"):
        st.error("🔑 Groq API key required (free at https://console.groq.com)")
        st.info("""
        **Get free API key:**
        1. Go to https://console.groq.com
        2. Sign up for free account  
        3. Get your API key
        4. Add to Streamlit secrets: `GROQ_API_KEY = "your_key"`
        """)
        return
    
    # Initialize scouts
    sme_scout = SMEDigitalTransformationScout()
    job_scout = JobPlatformScout()
    
    # Initialize session state
    if 'articles' not in st.session_state:
        st.session_state.articles = []
    if 'all_companies' not in st.session_state:
        st.session_state.all_companies = []
    
    # Create tabs for different functionalities
    tab1, tab2 = st.tabs(["🏢 SME Digital Transformation Scout", "💼 Job Platform Search"])
    
    with tab1:
        st.header("🏢 SME Digital Transformation Discovery")
        
        with st.sidebar:
            st.header("⚙️ SME Search Configuration")
            
            st.subheader("Target Industries")
            selected_industries = st.multiselect(
                "Select Industries:",
                sme_scout.INDUSTRIES,
                default=["Manufacturing", "BFSI", "Healthcare"]
            )
            
            st.subheader("Digital Technologies")
            selected_technologies = st.multiselect(
                "Focus Technologies:",
                sme_scout.DIGITAL_TECHNOLOGIES,
                default=["ERP", "AI", "RPA", "DMS"]
            )
            
            st.subheader("Search Settings")
            max_per_source = st.slider("Results per Search", 5, 20, 12)
            
            st.subheader("Analysis Settings")
            batch_size = st.slider("Batch Size for AI Analysis", 10, 50, 25)
            delay_between_batches = st.slider("Delay between batches (seconds)", 1, 10, 2)
            
            st.info("""
            **SME-Focused Features:**
            - Small-to-Medium Enterprise targeting
            - Revenue range analysis (1-250 crore)
            - Hiring trends 2025-2026
            - Kerala companies excluded
            - Batch processing for large datasets
            """)
        
        # Search Phase
        if st.button("🌐 Search for SME Articles", type="primary", use_container_width=True):
            if not selected_industries:
                st.error("❌ Please select at least one industry")
                return
                
            if not selected_technologies:
                st.error("❌ Please select at least one technology focus")
                return
            
            # Generate targeted SME search queries
            search_queries = sme_scout.build_sme_search_queries(selected_industries, selected_technologies)
            
            st.info(f"🔍 Using {len(search_queries)} targeted SME queries across {len(selected_industries)} industries")
            
            with st.spinner("🌐 Comprehensive SME digital transformation search in progress..."):
                # Perform hybrid search
                articles = sme_scout.hybrid_search(search_queries, max_per_source)
                st.session_state.articles = articles
                
                if not articles:
                    st.error("""
                    ❌ No articles found. Possible issues:
                    - Internet connectivity
                    - Search engines temporarily unavailable
                    - Try different industries or technologies
                    """)
                    return
                
                st.success(f"✅ Found {len(articles)} relevant SME articles")
                
                # Display search summary
                col1, col2 = st.columns(2)
                with col1:
                    google_count = len([a for a in articles if a['source'] == 'Google News'])
                    st.metric("Google News", google_count)
                with col2:
                    other_count = len([a for a in articles if a['source'] != 'Google News'])
                    st.metric("Other Sources", other_count)
        
        # Show article management if we have articles
        if st.session_state.articles:
            st.markdown("---")
            st.header("📄 Article Management")
            
            articles = st.session_state.articles
            st.info(f"📚 Total articles available: {len(articles)}")
            
            # Article preview
            with st.expander("📋 Preview SME Articles (First 10)"):
                for i, article in enumerate(articles[:10]):
                    st.write(f"**{i+1}. {article['title']}**")
                    st.write(f"Source: {article['source']} | Date: {article['date']}")
                    st.write(f"[Read more]({article['link']})")
                    st.markdown("---")
            
            # Analysis range selection
            st.subheader("🔍 AI Analysis Range")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                start_index = st.number_input("Start Index", min_value=0, max_value=len(articles)-1, value=0, key="sme_start")
            with col2:
                end_index = st.number_input("End Index", min_value=1, max_value=len(articles), value=min(100, len(articles)), key="sme_end")
            with col3:
                st.metric("Articles to Analyze", end_index - start_index)
            
            # Batch analysis options
            st.subheader("⚡ Batch Analysis Options")
            
            col1, col2 = st.columns(2)
            with col1:
                analyze_all = st.button("🚀 Analyze All Articles", use_container_width=True, key="analyze_all")
            with col2:
                analyze_range = st.button("🎯 Analyze Selected Range", use_container_width=True, type="primary", key="analyze_range")
            
            if analyze_all or analyze_range:
                if analyze_all:
                    articles_to_analyze = articles
                    st.info(f"🔄 Analyzing ALL {len(articles)} SME articles")
                else:
                    articles_to_analyze = articles[start_index:end_index]
                    st.info(f"🔄 Analyzing articles {start_index} to {end_index} ({len(articles_to_analyze)} articles)")
                
                # AI Analysis Phase
                st.markdown("---")
                st.header("🤖 AI Analysis Phase")
                
                with st.spinner("🤖 AI analyzing for SME digital transformation companies..."):
                    # Extract companies using Groq with batch processing
                    companies_data = sme_scout.extract_company_data_with_groq(
                        articles_to_analyze, 
                        batch_size=batch_size,
                        delay_between_batches=delay_between_batches
                    )
                    
                    if not companies_data:
                        st.error("""
                        ❌ No SME digital transformation companies extracted. This could mean:
                        - Articles don't contain specific SME digital transformation info
                        - Try expanding industry selection
                        - Adjust technology focus
                        - Increase number of articles analyzed
                        """)
                        return
                    
                    # Calculate relevance scores
                    for company in companies_data:
                        company['Relevance Score'] = sme_scout.calculate_sme_relevance_score(company)
                    
                    # Filter and rank companies
                    ranked_companies = sme_scout.filter_and_rank_sme_companies(companies_data)
                    
                    # Store in session state
                    if analyze_all:
                        st.session_state.all_companies = ranked_companies
                    else:
                        # Merge with existing companies, removing duplicates
                        existing_companies = st.session_state.all_companies
                        all_companies_dict = {}
                        
                        # Add existing companies to dict
                        for company in existing_companies:
                            all_companies_dict[company['Company Name']] = company
                        
                        # Add new companies, updating if exists
                        for company in ranked_companies:
                            all_companies_dict[company['Company Name']] = company
                        
                        st.session_state.all_companies = list(all_companies_dict.values())
                        st.session_state.all_companies.sort(key=lambda x: x['Relevance Score'], reverse=True)
                    
                    st.success(f"🎯 Found {len(ranked_companies)} SME companies in this analysis!")
                    st.success(f"💾 Total SME companies in database: {len(st.session_state.all_companies)}")
        
        # Show results if we have companies
        if st.session_state.all_companies:
            st.markdown("---")
            st.header("📈 SME Digital Transformation Results")
            
            companies = st.session_state.all_companies
            
            # Statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total SMEs", len(companies))
            with col2:
                confirmed_smes = len([c for c in companies if 'sme' in c['Company Size'].lower()])
                st.metric("Confirmed SMEs", confirmed_smes)
            with col3:
                hiring_smes = len([c for c in companies if 'hiring' in c['Hiring Trends 2025-2026'].lower()])
                st.metric("SMEs Hiring", hiring_smes)
            with col4:
                high_confidence = len([c for c in companies if c['Confidence'] == 'high'])
                st.metric("High Confidence", high_confidence)
            
            # Display insights
            sme_scout.display_sme_insights(companies)
            
            # Company details table
            st.subheader("🏢 SME Company Details")
            df = pd.DataFrame(companies)
            
            # Enhanced styling for SMEs
            def color_company_size(val):
                if 'sme' in str(val).lower() or 'small' in str(val).lower():
                    return 'background-color: #90EE90; color: black; font-weight: bold;'
                elif 'growing' in str(val).lower():
                    return 'background-color: #FFE4B5; color: black;'
                return ''
            
            def color_hiring_trends(val):
                if 'hiring' in str(val).lower() or 'active' in str(val).lower():
                    return 'background-color: #87CEEB; color: black; font-weight: bold;'
                return ''
            
            # Select and style relevant columns
            display_columns = ['Company Name', 'Industry', 'Revenue Range', 'Company Size', 
                              'Digital Transformation', 'Hiring Trends 2025-2026', 'Confidence', 'Relevance Score']
            
            display_df = df[display_columns] if all(col in df.columns for col in display_columns) else df
            
            styled_df = display_df.style.map(color_company_size, subset=['Company Size'])\
                                      .map(color_hiring_trends, subset=['Hiring Trends 2025-2026'])
            
            # Display the dataframe
            st.dataframe(
                styled_df,
                column_config={
                    "Relevance Score": st.column_config.ProgressColumn(
                        "SME Relevance",
                        help="How relevant this SME is to digital transformation",
                        format="%f",
                        min_value=0,
                        max_value=10,
                    )
                },
                use_container_width=True,
                hide_index=True,
                height=600
            )
            
            # Enhanced Output
            st.subheader("📋 Enhanced TSV Output - Copy Ready")
            enhanced_output = sme_scout.generate_enhanced_output(companies)
            st.code(enhanced_output, language='text')
            
            # Download button
            st.download_button(
                label="💾 Download Complete SME Data",
                data=enhanced_output,
                file_name=f"sme_digital_transformation_{datetime.now().strftime('%Y%m%d_%H%M')}.tsv",
                mime="text/tab-separated-values",
                use_container_width=True
            )
            
            # Clear data button
            if st.button("🗑️ Clear All Data", use_container_width=True, key="clear_sme"):
                st.session_state.articles = []
                st.session_state.all_companies = []
                st.rerun()
    
    with tab2:
        st.header("💼 Job Platform Search")
        st.markdown("Search for job announcements on platforms like LinkedIn, Naukri, Indeed, Glassdoor, etc.")
        
        with st.sidebar:
            st.header("🔍 Job Search Configuration")
            
            st.subheader("Search Type")
            search_type = st.radio(
                "Select Search Type:",
                ["Search by Company Names", "Search by Technologies"]
            )
            
            if search_type == "Search by Company Names":
                st.subheader("Company Names")
                company_input = st.text_area(
                    "Enter company names (one per line):",
                    placeholder="TCS\nInfosys\nWipro\nHCL\n...",
                    height=150
                )
                max_jobs_per_company = st.slider("Max jobs per company", 1, 20, 5)
                
            else:  # Search by Technologies
                st.subheader("Technologies")
                tech_input = st.text_area(
                    "Enter technologies (one per line):",
                    placeholder="ERP\nAI\nData Analytics\nRPA\nDMS\n...",
                    height=150
                )
                locations = st.text_input(
                    "Locations (comma separated):",
                    "India, Bangalore, Hyderabad, Pune, Chennai"
                )
                max_tech_jobs = st.slider("Max jobs per technology", 1, 30, 10)
        
        if search_type == "Search by Company Names":
            if st.button("🔍 Search Jobs by Company", type="primary", use_container_width=True):
                if not company_input.strip():
                    st.error("❌ Please enter at least one company name")
                else:
                    company_names = [name.strip() for name in company_input.split('\n') if name.strip()]
                    st.info(f"🔍 Searching jobs for {len(company_names)} companies...")
                    
                    with st.spinner("Searching job platforms..."):
                        job_listings = job_scout.search_jobs_by_company(company_names, max_jobs_per_company)
                    
                    if job_listings:
                        st.success(f"✅ Found {len(job_listings)} job listings")
                        
                        # Display job insights
                        st.subheader("📊 Job Search Insights")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            platforms = [job['Platform'] for job in job_listings]
                            platform_counts = pd.Series(platforms).value_counts()
                            st.metric("Job Platforms", len(platform_counts))
                        
                        with col2:
                            digital_roles = len([job for job in job_listings if job['Role Type'] == 'Digital Transformation'])
                            st.metric("Digital Transformation Roles", digital_roles)
                        
                        with col3:
                            companies_found = len(set([job['Company'] for job in job_listings]))
                            st.metric("Companies Found", companies_found)
                        
                        # Platform distribution
                        st.subheader("Platform Distribution")
                        if not platform_counts.empty:
                            st.bar_chart(platform_counts)
                        
                        # Job listings table
                        st.subheader("💼 Job Listings")
                        jobs_df = pd.DataFrame(job_listings)
                        
                        # Style the dataframe
                        def color_role_type(val):
                            if val == 'Digital Transformation':
                                return 'background-color: #90EE90; color: black; font-weight: bold;'
                            return ''
                        
                        def color_platform(val):
                            if val in ['LinkedIn', 'Naukri', 'Indeed']:
                                return 'background-color: #FFE4B5; color: black;'
                            return ''
                        
                        styled_jobs_df = jobs_df.style.map(color_role_type, subset=['Role Type'])\
                                                    .map(color_platform, subset=['Platform'])
                        
                        st.dataframe(
                            styled_jobs_df,
                            column_config={
                                "Link": st.column_config.LinkColumn("Job Link")
                            },
                            use_container_width=True,
                            hide_index=True,
                            height=600
                        )
                        
                        # Download jobs data
                        st.subheader("📋 Jobs TSV Output")
                        jobs_output = job_scout.generate_jobs_output(job_listings)
                        st.code(jobs_output, language='text')
                        
                        st.download_button(
                            label="💾 Download Jobs Data",
                            data=jobs_output,
                            file_name=f"job_listings_{datetime.now().strftime('%Y%m%d_%H%M')}.tsv",
                            mime="text/tab-separated-values",
                            use_container_width=True
                        )
                    else:
                        st.error("❌ No job listings found for the specified companies")
        
        else:  # Search by Technologies
            if st.button("🔍 Search Jobs by Technology", type="primary", use_container_width=True):
                if not tech_input.strip():
                    st.error("❌ Please enter at least one technology")
                else:
                    technologies = [tech.strip() for tech in tech_input.split('\n') if tech.strip()]
                    location_list = [loc.strip() for loc in locations.split(',') if loc.strip()]
                    
                    st.info(f"🔍 Searching {len(technologies)} technologies in {len(location_list)} locations...")
                    
                    with st.spinner("Searching job platforms for technology roles..."):
                        tech_jobs = job_scout.search_jobs_by_technology(technologies, location_list, max_tech_jobs)
                    
                    if tech_jobs:
                        st.success(f"✅ Found {len(tech_jobs)} technology job listings")
                        
                        # Display tech job insights
                        st.subheader("📊 Technology Job Insights")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            tech_counts = pd.Series([job['Technology'] for job in tech_jobs]).value_counts()
                            st.metric("Technologies Found", len(tech_counts))
                        
                        with col2:
                            companies_found = len(set([job['Company'] for job in tech_jobs]))
                            st.metric("Companies Hiring", companies_found)
                        
                        with col3:
                            platforms = [job['Platform'] for job in tech_jobs]
                            platform_counts = pd.Series(platforms).value_counts()
                            st.metric("Job Platforms", len(platform_counts))
                        
                        # Technology distribution
                        st.subheader("Technology Distribution")
                        if not tech_counts.empty:
                            st.bar_chart(tech_counts)
                        
                        # Tech job listings table
                        st.subheader("💻 Technology Job Listings")
                        tech_jobs_df = pd.DataFrame(tech_jobs)
                        
                        st.dataframe(
                            tech_jobs_df,
                            column_config={
                                "Link": st.column_config.LinkColumn("Job Link")
                            },
                            use_container_width=True,
                            hide_index=True,
                            height=600
                        )
                        
                        # Download tech jobs data
                        st.subheader("📋 Technology Jobs TSV Output")
                        tech_jobs_output = job_scout.generate_jobs_output(tech_jobs)
                        st.code(tech_jobs_output, language='text')
                        
                        st.download_button(
                            label="💾 Download Tech Jobs Data",
                            data=tech_jobs_output,
                            file_name=f"tech_jobs_{datetime.now().strftime('%Y%m%d_%H%M')}.tsv",
                            mime="text/tab-separated-values",
                            use_container_width=True
                        )
                    else:
                        st.error("❌ No technology job listings found")

if __name__ == "__main__":
    main()
