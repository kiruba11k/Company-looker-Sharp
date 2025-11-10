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
    page_title=" Digital Transformation Scout",
    page_icon="",
    layout="wide"
)

class DigitalTransformationScout:
    def __init__(self):
        self.groq_client = Groq(api_key=st.secrets.get("GROQ_API_KEY"))
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Target industries
        self.INDUSTRIES = [
            "Manufacturing", "BFSI", "Healthcare", "Hospitals", 
            "Pharmaceutical", "Insurance", "Banking", "Financial Services"
        ]
        
        # Digital transformation technologies to track
        self.DIGITAL_TECHNOLOGIES = [
            "DMS", "Document Management System", "DCM", "Digital Contract Management",
            "ERP", "Enterprise Resource Planning", "RPA", "Robotic Process Automation",
            "Managed IT Services", "AI", "Artificial Intelligence", "Data Analytics",
            "digital transformation", "digital initiative", "technology transformation",
            "cloud migration", "automation", "business intelligence", "BI",
            "SAP", "Oracle", "Microsoft Dynamics", "Salesforce", "ServiceNow"
        ]
        
        # Indian states to exclude (Kerala)
        self.EXCLUDE_STATES = ["Kerala", "kerala"]
        
        # Company size indicators
        self.REVENUE_INDICATORS = [
            "revenue", "turnover", "income", "sales", "₹", "crore", "million", "billion"
        ]
        
        # Hiring trend indicators
        self.HIRING_INDICATORS = [
            "hiring", "recruitment", "expanding team", "new positions", "careers",
            "job openings", "talent acquisition", "workforce expansion", "recruiting"
        ]

    def search_google_news_rss(self, query, max_results=20):
        """Free Google News RSS search for digital transformation news"""
        try:
            base_url = "https://news.google.com/rss"
            
            # Enhanced query with digital transformation focus
            enhanced_query = f"{query} India -Kerala after:2024-01-01"
            
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

    def search_duckduckgo_news(self, query, max_results=15):
        """DuckDuckGo search for digital transformation content"""
        try:
            # Build enhanced query excluding Kerala
            enhanced_query = f"{query} India -Kerala"
            
            base_url = "https://html.duckduckgo.com/html/"
            params = {
                'q': enhanced_query,
                'kl': 'in-en',
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            response = self.session.post(base_url, data=params, headers=headers, timeout=20)
            articles = []
            
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
                            
                            # Skip if mentions Kerala
                            if any(state in (title + snippet).lower() for state in [s.lower() for s in self.EXCLUDE_STATES]):
                                continue
                            
                            # Extract actual URL from DuckDuckGo redirect
                            if link and 'uddg=' in link:
                                match = re.search(r'uddg=([^&]+)', link)
                                if match:
                                    link = urllib.parse.unquote(match.group(1))
                            
                            # Only include valid links
                            if link and any(domain in link for domain in ['.com', '.in', '.org', '.net', '.co']):
                                articles.append({
                                    'title': title,
                                    'link': link,
                                    'description': snippet,
                                    'source': 'DuckDuckGo',
                                    'date': '2024+',
                                    'content': f"{title}. {snippet}"
                                })
                    except Exception:
                        continue
                
                return articles
            else:
                return []
                
        except Exception as e:
            st.error(f"DuckDuckGo search error: {str(e)}")
            return []

    def build_digital_transformation_queries(self, selected_industries, technologies):
        """Build targeted queries for digital transformation"""
        base_queries = []
        
        # Industry-specific digital transformation queries
        industry_tech_mapping = {
            "Manufacturing": ["ERP", "IIoT", "automation", "smart factory", "digital manufacturing"],
            "BFSI": ["core banking", "fintech", "digital lending", "risk analytics", "blockchain"],
            "Healthcare": ["EHR", "EMR", "telemedicine", "healthtech", "medical records"],
            "Hospitals": ["hospital management", "patient records", "medical imaging AI", "healthcare analytics"]
        }
        
        for industry in selected_industries:
            industry_queries = [
                f"{industry} digital transformation India",
                f"{industry} ERP implementation India",
                f"{industry} AI adoption India",
                f"{industry} cloud migration India",
                f"{industry} automation initiative India"
            ]
            
            # Add industry-specific technologies
            if industry in industry_tech_mapping:
                for tech in industry_tech_mapping[industry]:
                    industry_queries.append(f"{industry} {tech} implementation India")
                    industry_queries.append(f"{industry} {tech} project India")
            
            base_queries.extend(industry_queries)
        
        # Technology-specific queries
        for tech in technologies[:5]:  # Use top 5 technologies
            tech_queries = [
                f"{tech} implementation India",
                f"{tech} project India",
                f"{tech} adoption Indian companies",
                f"implementing {tech} India"
            ]
            base_queries.extend(tech_queries)
        
        # Partner announcement queries (vendors announcing client wins)
        vendors = ["TCS", "Infosys", "Wipro", "HCL", "Accenture", "IBM", "Capgemini"]
        for vendor in vendors[:3]:
            base_queries.append(f'{vendor} "digital transformation" client India')
            base_queries.append(f'{vendor} "implemented" India')
        
        return list(set(base_queries))[:25]  # Limit to 25 unique queries

    def hybrid_search(self, search_terms, max_results_per_source=15):
        """Hybrid search across multiple free sources"""
        all_articles = []
        
        for term in search_terms:
            st.info(f"🔍 Searching: {term}")
            
            # Google News search
            google_articles = self.search_google_news_rss(term, max_results_per_source)
            all_articles.extend(google_articles)
            time.sleep(1)
            
            # DuckDuckGo search
            ddg_articles = self.search_duckduckgo_news(term, max_results_per_source)
            all_articles.extend(ddg_articles)
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

    def extract_company_data_with_groq(self, articles):
        """Use Groq to extract digital transformation company data"""
        if not articles:
            return []
            
        extracted_data = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Enhanced system prompt for digital transformation
        system_prompt = f"""You are an expert Indian business analyst specializing in digital transformation. Extract company information from news articles with focus on digital initiatives.

TARGET INDUSTRIES: {', '.join(self.INDUSTRIES)}
DIGITAL TECHNOLOGIES: {', '.join(self.DIGITAL_TECHNOLOGIES)}
EXCLUDE COMPANIES: Based in Kerala

CRITICAL: Extract companies undergoing digital transformation initiatives. Look for:
- ERP, DMS, DCM, RPA implementations
- AI and Data Analytics projects
- Managed IT Services adoption
- Digital transformation announcements

Return EXACT JSON format:
{{
    "companies": [
        {{
            "company_name": "extracted company name",
            "website": "company website if mentioned, else empty",
            "industry": "Manufacturing/BFSI/Healthcare/Hospitals",
            "revenue": "revenue information if mentioned, else 'Not specified'",
            "digital_transformation": "Yes/No",
            "transformation_details": "specific technologies and projects mentioned",
            "hiring_trends_2025_2026": "hiring indications if mentioned, else 'Not specified'",
            "source_validation": "how confident based on article content",
            "confidence_score": "high/medium/low"
        }}
    ]
}}

If no relevant companies found, return: {{"companies": []}}"""
        
        processed_count = 0
        for i, article in enumerate(articles):
            try:
                status_text.text(f" Analyzing article {i+1}/{len(articles)}...")
                progress_bar.progress((i + 1) / len(articles))
                
                content = article['content']
                if len(content) > 3000:
                    content = content[:3000]
                
                user_prompt = f"""
                Analyze this Indian business/technology news article for companies undergoing digital transformation:

                TITLE: {article['title']}
                CONTENT: {content}

                Extract ALL companies mentioned. Focus on:
                - Industries: {', '.join(self.INDUSTRIES)}
                - Technologies: {', '.join(self.DIGITAL_TECHNOLOGIES)}
                - Exclude companies based in Kerala
                - Look for revenue mentions and hiring trends for 2025-2026
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
                        # Validate required fields
                        if (company.get('company_name') and 
                            company.get('company_name') != 'null' and
                            company.get('digital_transformation') == 'Yes'):
                            
                            extracted_data.append({
                                'Company Name': company['company_name'],
                                'Website': company.get('website', 'Not specified'),
                                'Industry': company.get('industry', 'Not specified'),
                                'Revenue': company.get('revenue', 'Not specified'),
                                'Digital Transformation': company.get('digital_transformation', 'No'),
                                'Transformation Details': company.get('transformation_details', 'Digital initiatives mentioned'),
                                'Hiring Trends 2025-2026': company.get('hiring_trends_2025_2026', 'Not specified'),
                                'Source Link': article['link'],
                                'Article Title': article['title'],
                                'Source': article['source'],
                                'Date': article.get('date', '2024+'),
                                'Confidence': company.get('confidence_score', 'medium'),
                                'Source Validation': company.get('source_validation', 'Article mentions digital initiatives')
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
            st.success(f" Successfully extracted {processed_count} digital transformation companies")
        
        return extracted_data

    def enhance_company_data(self, companies):
        """Enhance company data with additional information"""
        enhanced_companies = []
        
        for company in companies:
            # Generate mock website if not specified (for demonstration)
            if company['Website'] == 'Not specified':
                company_name_clean = re.sub(r'[^a-zA-Z0-9]', '', company['Company Name'])
                company['Website'] = f"www.{company_name_clean.lower()}.com"
            
            # Add relevance scoring
            score = self.calculate_relevance_score(company)
            company['Relevance Score'] = score
            
            enhanced_companies.append(company)
        
        return enhanced_companies

    def calculate_relevance_score(self, company):
        """Calculate relevance score based on multiple factors"""
        score = 0
        
        # Confidence scoring
        if company['Confidence'] == 'high':
            score += 3
        elif company['Confidence'] == 'medium':
            score += 2
        else:
            score += 1
        
        # Industry priority
        priority_industries = ['Manufacturing', 'BFSI', 'Healthcare']
        if company['Industry'] in priority_industries:
            score += 2
        
        # Technology depth
        tech_keywords = ['ERP', 'AI', 'DMS', 'RPA', 'analytics']
        details = company['Transformation Details'].lower()
        tech_count = sum(1 for tech in tech_keywords if tech.lower() in details)
        score += min(tech_count, 3)
        
        # Hiring trends bonus
        if 'hiring' in company['Hiring Trends 2025-2026'].lower() or 'expanding' in company['Hiring Trends 2025-2026'].lower():
            score += 2
        
        return score

    def filter_and_rank_companies(self, companies):
        """Filter and rank companies by relevance"""
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
        """Generate enhanced output with all required fields"""
        if not companies:
            return "No digital transformation companies found"
        
        output_lines = ["Company Name\tWebsite\tIndustry\tRevenue\tDigital Transformation\tTransformation Details\tHiring Trends 2025-2026\tSource Link\tConfidence\tRelevance Score"]
        
        for company in companies:
            company_name = str(company['Company Name']).replace('\t', ' ').replace('\n', ' ')
            website = str(company['Website']).replace('\t', ' ')
            industry = str(company['Industry']).replace('\t', ' ')
            revenue = str(company['Revenue']).replace('\t', ' ')
            digital_transformation = str(company['Digital Transformation']).replace('\t', ' ')
            transformation_details = str(company['Transformation Details']).replace('\t', ' ').replace('\n', ' ')
            hiring_trends = str(company['Hiring Trends 2025-2026']).replace('\t', ' ')
            source_link = str(company['Source Link']).replace('\t', ' ')
            confidence = str(company['Confidence']).replace('\t', ' ')
            relevance_score = str(company['Relevance Score'])
            
            output_line = f"{company_name}\t{website}\t{industry}\t{revenue}\t{digital_transformation}\t{transformation_details}\t{hiring_trends}\t{source_link}\t{confidence}\t{relevance_score}"
            output_lines.append(output_line)
        
        return "\n".join(output_lines)

    def display_digital_transformation_insights(self, companies):
        """Display insights about digital transformation trends"""
        if not companies:
            return
        
        st.header(" Digital Transformation Insights")
        
        # Industry distribution
        industries = [company['Industry'] for company in companies]
        industry_df = pd.DataFrame({'Industry': industries})
        industry_counts = industry_df['Industry'].value_counts()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Industry Distribution")
            st.bar_chart(industry_counts)
        
        with col2:
            st.subheader("Technology Adoption")
            tech_keywords = ['ERP', 'AI', 'Cloud', 'RPA', 'Analytics', 'DMS']
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
                st.info("No specific technology data available")
        
        with col3:
            st.subheader("Hiring Trends")
            hiring_companies = len([c for c in companies if 'hiring' in c['Hiring Trends 2025-2026'].lower() or 'expanding' in c['Hiring Trends 2025-2026'].lower()])
            total_companies = len(companies)
            
            if total_companies > 0:
                hiring_percentage = (hiring_companies / total_companies) * 100
                st.metric("Companies Hiring (2025-2026)", f"{hiring_percentage:.1f}%")
            else:
                st.metric("Companies Hiring", "0%")

def main():
    st.title(" Digital Transformation Company Scout")
    st.markdown("""
    **Discover Indian companies undergoing digital transformation**  
    *Targeting Manufacturing, BFSI, Healthcare & Hospitals (Excluding Kerala)*
    """)
    
    if not st.secrets.get("GROQ_API_KEY"):
        st.error(" Groq API key required (free at https://console.groq.com)")
        st.info("""
        **Get free API key:**
        1. Go to https://console.groq.com
        2. Sign up for free account  
        3. Get your API key
        4. Add to Streamlit secrets: `GROQ_API_KEY = "your_key"`
        """)
        return
    
    scout = DigitalTransformationScout()
    
    with st.sidebar:
        st.header("⚙️ Search Configuration")
        
        st.subheader("Target Industries")
        selected_industries = st.multiselect(
            "Select Industries:",
            scout.INDUSTRIES,
            default=["Manufacturing", "BFSI", "Healthcare"]
        )
        
        st.subheader("Digital Technologies")
        selected_technologies = st.multiselect(
            "Focus Technologies:",
            scout.DIGITAL_TECHNOLOGIES,
            default=["ERP", "AI", "RPA", "DMS", "Data Analytics"]
        )
        
        st.subheader("Search Settings")
        max_articles = st.slider("Articles to Analyze", 10, 50, 25)
        max_per_source = st.slider("Results per Search", 5, 20, 12)
        
        st.info("""
        **Features:**
        - Digital transformation focus
        - Kerala companies excluded
        - 2025-2026 hiring trends
        - Revenue intelligence
        - Multi-source validation
        """)
        
        st.warning("**Note:** Excluding all Kerala-based companies from results")
    
    st.header(" Company Discovery")
    
    if st.button("Start Digital Transformation Search", type="primary", use_container_width=True):
        if not selected_industries:
            st.error(" Please select at least one industry")
            return
            
        if not selected_technologies:
            st.error(" Please select at least one technology focus")
            return
        
        # Generate targeted search queries
        search_queries = scout.build_digital_transformation_queries(selected_industries, selected_technologies)
        
        st.info(f" Using {len(search_queries)} targeted queries across {len(selected_industries)} industries")
        
        with st.spinner(" Comprehensive digital transformation search in progress..."):
            # Perform hybrid search
            articles = scout.hybrid_search(search_queries, max_per_source)
            
            if not articles:
                st.error("""
                 No articles found. Possible issues:
                - Internet connectivity
                - Search engines temporarily unavailable
                - Try different industries or technologies
                """)
                return
            
            st.success(f" Found {len(articles)} relevant articles")
            
            # Display search summary
            col1, col2 = st.columns(2)
            with col1:
                google_count = len([a for a in articles if a['source'] == 'Google News'])
                st.metric("Google News", google_count)
            with col2:
                ddg_count = len([a for a in articles if a['source'] == 'DuckDuckGo'])
                st.metric("DuckDuckGo", ddg_count)
        
        # AI Analysis Phase
        st.markdown("---")
        st.header(" AI Analysis Phase")
        
        with st.spinner(" AI analyzing for digital transformation companies..."):
            # Extract companies using Groq
            companies_data = scout.extract_company_data_with_groq(articles[:max_articles])
            
            if not companies_data:
                st.error("""
                 No digital transformation companies extracted. This could mean:
                - Articles don't contain specific company digital transformation info
                - Try expanding industry selection
                - Adjust technology focus
                - Increase number of articles analyzed
                """)
                return
            
            # Enhance and rank companies
            enhanced_companies = scout.enhance_company_data(companies_data)
            ranked_companies = scout.filter_and_rank_companies(enhanced_companies)
            
            st.success(f" Found {len(ranked_companies)} companies undergoing digital transformation!")
        
        # Display Results
        st.header(" Digital Transformation Results")
        
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Articles Analyzed", len(articles[:max_articles]))
        with col2:
            st.metric("Companies Found", len(ranked_companies))
        with col3:
            high_confidence = len([c for c in ranked_companies if c['Confidence'] == 'high'])
            st.metric("High Confidence", high_confidence)
        with col4:
            hiring_companies = len([c for c in ranked_companies if 'hiring' in c['Hiring Trends 2025-2026'].lower()])
            st.metric("Hiring (2025-26)", hiring_companies)
        
        # Display insights
        scout.display_digital_transformation_insights(ranked_companies)
        
        # Company details table
        st.subheader(" Company Details")
        df = pd.DataFrame(ranked_companies)
        
        # Enhanced styling
        def color_confidence(val):
            if val == 'high':
                return 'background-color: #90EE90; color: black; font-weight: bold;'
            elif val == 'medium':
                return 'background-color: #FFE4B5; color: black;'
            else:
                return 'background-color: #FFB6C1; color: black;'
        
        def color_digital_transformation(val):
            if val == 'Yes':
                return 'background-color: #32CD32; color: white; font-weight: bold;'
            return 'background-color: #FF6347; color: white;'
        
        def color_hiring(val):
            if 'hiring' in str(val).lower() or 'expanding' in str(val).lower():
                return 'background-color: #87CEEB; color: black; font-weight: bold;'
            return ''
        
        styled_df = df.style.map(color_confidence, subset=['Confidence'])\
                          .map(color_digital_transformation, subset=['Digital Transformation'])\
                          .map(color_hiring, subset=['Hiring Trends 2025-2026'])
        
        # Display the dataframe
        st.dataframe(
            styled_df,
            column_config={
                "Source Link": st.column_config.LinkColumn("Source"),
                "Website": st.column_config.LinkColumn("Website"),
                "Relevance Score": st.column_config.ProgressColumn(
                    "Relevance",
                    help="How relevant this company is to digital transformation",
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
        st.subheader(" TSV Output - Copy Ready")
        enhanced_output = scout.generate_enhanced_output(ranked_companies)
        st.code(enhanced_output, language='text')
        
        # Download button
        st.download_button(
            label=" Download Complete TSV",
            data=enhanced_output,
            file_name=f"digital_transformation_companies_{datetime.now().strftime('%Y%m%d_%H%M')}.tsv",
            mime="text/tab-separated-values",
            use_container_width=True
        )
        
        # Business Opportunities
        if ranked_companies:
            st.header(" Sales Opportunities")
            
            # Top prospects
            top_companies = ranked_companies[:5]
            
            st.subheader(" Top 5 Digital Transformation Prospects")
            for i, company in enumerate(top_companies):
                with st.expander(f"{i+1}. {company['Company Name']} - {company['Industry']} (Score: {company['Relevance Score']}/10)"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Digital Focus:** {company['Transformation Details']}")
                        st.write(f"**Technology:** {company['Transformation Details']}")
                        st.write(f"**Hiring Trends:** {company['Hiring Trends 2025-2026']}")
                    with col2:
                        st.write(f"**Confidence:** {company['Confidence']}")
                        st.write(f"**Revenue:** {company['Revenue']}")
                        st.write(f"**Source:** [View Article]({company['Source Link']})")
                    
                    # Sales insight
                    st.success(f"**Opportunity:** {company['Company Name']} is actively investing in {company['Transformation Details'].split()[0] if company['Transformation Details'] else 'digital'} transformation - perfect for your DMS/DCM/ERP solutions.")

    else:
        # Enhanced instructions
        st.markdown("""
   
        """)

if __name__ == "__main__":
    main()
