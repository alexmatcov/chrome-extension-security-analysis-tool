#!/usr/bin/env python3
"""
Extract suspicious extension IDs from the EmPoWeb paper and check against 
a single JSON file called "all_extensions_ranked.json".
"""

import json
from pathlib import Path

def extract_suspicious_extension_ids():
    """Extract all suspicious extension IDs mentioned in the paper."""
    
    # Chrome Extensions from Table IX
    chrome_extensions = [
        "fimckmjeammfdcpldmcigeojkkmeeian",
        "fidaihkgnbcbkkdaoebdionfjenegede", 
        "hnkmipajjgbclkombnmigfnpekddlhlh",
        "fajjnmbcianlnhmngmabhgkmgdindlha",
        "efajnkcfjjkcodbhkhaigkffdleomnag",
        "hoobpdoclliidciecjifpikpnopjpmkh",
        "kjfjdocojijlledbaanbhpcnkoimghal",
        "pfofjhnkanlacmgfgjohncmgemffkldl",
        "gooecknlakggnppmhfpopneedjconjjp",
        "bdiogkcdmlehdjfandmfaibbkkaicppk",
        "pgbjjemkcflenaakhiehfdmcdnlnlpbl",
        "hdanmfijddamndfaabibmcafmnhhmebi",
        "hpmeebiiihmjelpjmmemlihhcacflflc",
        "oejnkhmeilmiplpmenkegjaibnjbappo",
        "jkoegdibpkleifbkojmplebjhfllkckn",
        "aopfgjfeiimeioiajeknfidlljpoebgc",
        "hlagecmhpppmpfdifmigdglnhcpnohib",
        "kpgdinlfgnkbfkmffilkgmeahphehegk",
        "bjjpnhdlhpfdebcbhdlmecafnokpjpce",
        "bmiedopcajpcehbbfglefijfmmndcaoa",
        "jegnjmcegcpodciadcoeneecmkiccfgi",
        "jnhibbjmekoijdjaopflcjbjieamifhh",
        "jpkfmllgncphdgojhkbcjidgeabaible",
        "ilcpdgfepihaomggobhmfiimflngbcoh",
        "jpcebpeheognnbogfkpllmmdnimjffdb",
        "cnkgdfnjmgamkcpjdljdncfjcegpgcdg",
        "cfddhmlokgokhcmepddjooekhmgmgfld",
        "efhgmgomhamkkmjbgmcpgjnabcfpnaek",
        "djhfcchmdelggndcpkgbanfhnpbbijdb",
        "fhlkioimlijffnblckmdikkadobdmlgn",
        "angncidddapgcmohkdmhidfleomhmfgi",
        "lndhlcaobijohmgoikmgpgbhepkbhpkl",
        "olpheomfiimdonpboopcailehdagfhaa",
        "idkghekmllmjgnmbohakcddgcclanlca",
        "mhdhcccejcjfanablmohbpdbepdkokkj",
        "plfffminkgohddbooidppccppgelajfp",
        "cboekbiaoabkhgjdclenjpipclabkdga",
        "ekeefjfdbaakgbfbagacmckiedkmakem",
        "lbjbbkhljiimahdeknpckaoiinopofhl",
        "ijmbknjhacbaeeoamjajoolgjgdbpkko",
        "hihakjfhbmlmjdnnhegiciffjplmdhin",
        "cfbodcmobhpfbjhbennacnanbmpbcfkd",
        "ommfijfafanajffiijecdlfjlbgpmgpl",
        "okgfglgogpkomipfflpajohdkaflndoh",
        "iiabjaofopjooifoclbpdmffjlgbplod",
        "mcdjehgaflnlmilhefigdkldfdnembhk",
        "lfekjajdgncmkajdpiadkkhhpblngnlc",
        "gkfpnohhmkonpkkpdbebccbgnajfgpjp",
        "pkkbbimilpjmghfhhppamgigileopnkc",
        "emiplbkkiabideffmpogkbbogkmofgph",
        "eadbjnlpeabhbllkljhifinhfelhimha",
        "ngegklmoecgejlbkiieccocmpmpmfhim",
        "iogibhaacmieogkdgebfbjgoofdlcmgb",
        "ooeealgadmhdnhebkhhbbcmckehpomcj",
        "dnohbnpecjinmdpeikpnmheeepnapfci",
        "pgmcojeijjhacgkkjaakdafmloncpema",
        "hacopcfnbokiahlppemnlneooamldola",
        "bpkphnbpiagbpinglgejckickdgaghjo",
        "fheihcbdclkdoeadmjfggiamjgkippli",
        "llelondjpcjljnjihdflhpclcpbiaiba",
        "pnbfclligibfgdknphcodpbcejnkhffp",
        "eihbcgffjehfcgafjljohecmadcefoji",
        "empgohlokhdhhchkenknobacofijiffg",
        "aefmgkhgcmdljpfijlohmbhkhflmbmfi",
        "dhjhphjhpcelebeagllljbfpipdfkhgi",
        "jeabbgpkliknjiacfkfglknajloappkh"
    ]
    
    # Fabasoft Extensions from Table VI
    fabasoft_extensions = [
        "ajlbdflhaaflcepndpkdgejimggjcpnm",
        "ngbcdblbfdpjgpmgfagkfofcjbnggfgn",
        "pdhjoolhbkmlgjfedckdhiknnoabbnkk",
        "hiejidhjgjpelfgldfhmnaoahnephhfg",
        "icjlkccflchmagmkfidekficomdnlcig"
    ]
    
    # HD Wallpapers Extensions from Table III (fliptab.io)
    hd_wallpaper_extensions = [
        "bddmmehmgpjhhmbbmngdjhlednmkbken",
        "cajmbfbhhfelhgolhldhhodkclpakcfe",
        "cepmfckfppjpbkjgnpokojedlngflnca",
        "clkodoejadlbjaopcjoijihebbgipjff",
        "dekpebffaadijeaogggfhjemdbjgbcao",
        "dkpndikhfepllbpaafgcelembimabofo",
        "eeiedbnahjonkmimigblgchlefcklhok",
        "efdddbobcofamdjmekphjlhgmcnhobbp",
        "ehmhopjniedignnkdeijmpmodhcppgif",
        "eilbnnflfpkhhfmhmlhflhecceajpkcj",
        "fieoemdbopiialnojhifcndkenhjkbmm",
        "fkpmpnljocdllgmplhnmjhjmmilbnofj",
        "gfgchcclfmppnfoakdlhgdhnolbpiedf",
        "glfbbjdfmmlanpikdedpjoeimlijjcjj",
        "hmbedbiicehadpbhbipafffieolpjolh",
        "hocncjdhccalpmblkpagbmjebkfkibbm",
        "iamlligjelallbdddajmbojjjhadkmcf",
        "jcffnpjkbahanenhcnhhdfopkjlpflfm",
        "jokpapkhjeahjbkemfjfhjgcogmbcpoi",
        "kkejopfphkmldfpdmcljfoinfcljijjf",
        "klfeojnepdoehgddffbcjiamcjjahmgj",
        "lbfidebeingoondbmpeapjoeeoloanak",
        "lgphbplfjpemcghfcoajehcmikflcbbd",
        "lmbcpiodajlbgmjbiajgcjdalgbofcbn",
        "loggojfoonblkkhkjpijapeheoogagki",
        "lpkfidfkgflpbakdnhpojiejlpdanknh",
        "mgmodhbknbfmpjmilankiffnjbelcipo",
        "mibaeahdcconphmdndbeipegldkkbcjh",
        "odpiaedkmdpcheddbkilnkelhhocoenn",
        "pfdaccgdljiifplhfnjcacapfedngonb",
        "afddmpnodjaifgjibafjcbfaplnoipei"
    ]
    
    # VK Download Extensions from Table IV
    vk_download_extensions = [
        "nfhipbkhabgmkhahoaagkcgppcjikjgl",
        "idenapkfefkbknhbmfgeaclpcpbhcnbe",
        "fnnlocjimhjpmgfjhjamdkjhemfhkhjo",
        "lmlnplkfbiihcpkghkkmfefjdaccmbcc",
        "kbiocjbkoohjjkkeaafiemjeidgalllh",
        "dccmnjciogmmahaogjgkocongokmieog",
        "ekfkljjojhnnhfedepfnbhhfjklagngk",
        "hhfgpbjpilbbaomjmdpnfchbpipehiif",
        "pgajmafmbajahclonccaoaoleghhnpam",
        "ipeeopcjpgcbgnfogjlickeilmkbonen",
        "jfpmehlefcchhhmlmennihbbihaolabk",
        "kcollknpphnodcjdkcmgpjmlbaenabao",
        "backekeabechifnekobfachchocbmjag",
        "mfpbgndgoogfplejodpbhnfmaibnalkf",
        "ojhheobonaamlhlcdngacakdcigpeokl",
        "mienmjdbnnpaigifneeiifdbjkdgelha",
        "amaobfendgcolppeioeageanmillkmkc"
    ]
    
    # Atavi Extensions from Table V
    atavi_extensions = [
        "iglbnbabjdfaobglhonmnlkdbommiebd",
        "knflcnelciofoghldagpknelepafjeif",
        "lamnafpjcnoclihgpefhdbefcmjikhaj",
        "jffjjdoccjiflmckicphblggbppfgklk",
        "ofmacdiceehcibkfednmgpkhgfhpacgi",
        "jpchabeoojaflbaajmjhfcfiknckabpo"
    ]
    
    # Storage Extensions from Table VII (any application access)
    storage_any_extensions = [
        "eljhpoopiapggnlfcilpbihgbgbpnkgd",
        "akhamklknibionleflabebgeikdookmp",
        "hebabhddakflgmlhgefakkfkciijliie",
        "ilgdjidfijkaengnhpeoneiagigajhco",
        "ohdihpdgfenligmhnmldmiabdhflokkh",
        "abenhehmjmoifipfpjeaejpbeeihnokp",
        "ackpndpapmikcoklmcbigfgkiemohddk",
        "ceogcehidijhepckebfifkpfogkajdkg",
        "cgijoonmpaboophnagdckdcekmpfokel",
        "dhcfokhhmhenbfmeflifppiedabfggkj",
        "dhcmolikocplmafolinkncghmahimooh",
        "eamjolanjdmgochipodfokkfjaeifhon",
        "efhbachoakbcmbcmfffdgphbpcbldjac",
        "fecipnolpdcmoidbjbnakpjgfikbnaik",
        "gnnagpehbmfalanfjadamobejlldgedo",
        "ijdfpccaiklfhpnamolipbjjijilmhli",
        "khjhfgcimhcnaimdbgjbnbhcojkoceoc",
        "niceocbendibobemckcagggppphheomc",
        "okcfiidnmioajibmhhjpiomgejajiafa",
        "pjjceionkajpednnegoanjjdlhbgkkpc",
        "pjojmkmdealampgchopkfbejihpimjia"
    ]
    
    # Storage Extensions from Table VIII (specific applications)
    storage_specific_extensions = [
        "lpkhcobfjeidpkllbeagkkmmjgbmpfch",
        "eggdmhdpffgikgakkfojgiledkekfdce",
        "jmllflbhbembffempimjdbgnaodpoihh",
        "jmlnhlclbpfcbkaoaegfigepaffoankc",
        "gaoiiiehelhpkmpkolndijhiogfholcc",
        "ghldlmcbffbcnoofadgcapodmpiimflj",
        "jpgadigdffhcjldfkanacncocacekkie",
        "peiajekggpiihnhphljoikpjeaahkdcn",
        "bnfboihohdckgijdkplinpflifbbfmhm",
        "aclhfmpoahihmhhacaekgcbjaeojnifa",
        "hcdfoeppbchkbbpplllggbjkkfokifej",
        "hddnlanhlmifafibmlabomkkkobcmchj",
        "lhjajgnfmiliphkioedlmbfcdkhdhnkc",
        "bmdlalnebjigindhobniianfmhakfelf",
        "dadggmdmhmfkpglkfpkjdmlendbkehoh",
        "pbpfgdgddpnbjcbpofmdanfbbigocklj",
        "ilpkhojfiejdbkgcjbmllngjebdoehim",
        "cfnjeahambijfdljfacldifapdcklhnj",
        "cjkbjhfhpbmnphgbppkbcidpmmbhaifa",
        "ddiaadobgihkgefcaajmkjgmnjakiamn",
        "dienbdhbgkpddlgaceopelifcjpmkeha",
        "dnpdkejhfeeipmklhlkdjaoakbkjkkjn",
        "gmjdaaahidcimfaipifeoekglllgdllb",
        "kfodnoaejimmmphonklghkimhnhhgbce"
    ]
    
    
    # Combine all extensions
    all_suspicious_ids = (
        chrome_extensions + 
        fabasoft_extensions + 
        hd_wallpaper_extensions + 
        vk_download_extensions + 
        atavi_extensions + 
        storage_any_extensions + 
        storage_specific_extensions
    )
    
    # Remove duplicates and sort
    return sorted(list(set(all_suspicious_ids)))

def save_suspicious_ids(extension_ids, filename="suspicious_extension_ids.txt"):
    """Save the suspicious extension IDs to a file."""
    with open(filename, 'w') as f:
        f.write("# Suspicious Extension IDs from EmPoWeb Paper\n")
        f.write("# Total: {} extensions\n\n".format(len(extension_ids)))
        for ext_id in extension_ids:
            f.write(f"{ext_id}\n")
    print(f"Saved {len(extension_ids)} suspicious extension IDs to {filename}")

def check_risk_analysis_file(suspicious_ids, file_path="all_extensions_ranked.json"):
    """Check for suspicious extensions in the risk analysis JSON file."""
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"Error: File '{file_path}' does not exist")
        return
    
    print(f"Analyzing file: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return
    
    # Extract analysis summary
    if 'analysis_summary' in data:
        summary = data['analysis_summary']
        print(f"   Analysis Summary:")
        print(f"   Total Extensions: {summary.get('total_extensions_analyzed', 'Unknown'):,}")
        print(f"   Extensions with Risk: {summary.get('extensions_with_risk', 'Unknown'):,}")
        print(f"   Zero Risk Extensions: {summary.get('extensions_with_zero_risk', 'Unknown'):,}")
        print(f"   Highest Risk Score: {summary.get('highest_risk_score', 'Unknown')}")
        print(f"   Average Risk Score: {summary.get('average_risk_score', 'Unknown'):.2f}")
        print()
    
    # Get extensions data
    extensions_data = data.get('extensions', [])
    
    if not isinstance(extensions_data, list):
        print(f"Error: Expected list of extensions, got {type(extensions_data)}")
        return
    
    print(f"Found {len(extensions_data)} extensions in the analysis file")
    
    # Find matches
    suspicious_set = set(suspicious_ids)
    matches = []
    
    for ext in extensions_data:
        if isinstance(ext, dict):
            ext_id = ext.get('extension_id')
            
            if ext_id and ext_id in suspicious_set:
                matches.append({
                    'id': ext_id,
                    'rank': ext.get('rank', 'Unknown'),
                    'data': ext
                })
    
    # Display results
    if matches:
        print(f"\nFOUND {len(matches)} SUSPICIOUS EXTENSIONS:")
        print("=" * 80)
        
        # Sort by rank
        matches.sort(key=lambda x: x['rank'] if isinstance(x['rank'], int) else float('inf'))
        
        for match in matches:
            ext_data = match['data']
            print(f"RANK #{match['rank']}")
            print(f"Extension ID: {match['id']}")
            print(f"Total Risk Score: {ext_data.get('total_risk_score', 'Unknown')}")
            
            # Show risk breakdown
            if 'risk_breakdown' in ext_data:
                breakdown = ext_data['risk_breakdown']
                print(f"Risk Breakdown:")
                print(f"  • Permission Risk: {breakdown.get('permission_risk', 0)}")
                print(f"  • Host Risk:       {breakdown.get('host_risk', 0)}")
                print(f"  • Metadata Risk:   {breakdown.get('metadata_risk', 0)}")
                print(f"  • Bonus Risk:      {breakdown.get('bonus_risk', 0)}")
            
            # Show risk factors
            if 'risk_factors' in ext_data:
                factors = ext_data['risk_factors']
                print(f"Risk Factors:")
                
                host_perms = factors.get('host_permissions', [])
                if host_perms:
                    print(f"  • Host Permissions: {', '.join(host_perms)}")
                else:
                    print(f"  • Host Permissions: None")
                
                print(f"  • Externally Connectable: {factors.get('externally_connectable', False)}")
                print(f"  • Content Scripts: {factors.get('content_scripts', False)}")
            
            # Calculate risk level based on score
            risk_score = ext_data.get('total_risk_score', 0)
            if isinstance(risk_score, (int, float)):
                if risk_score >= 1000:
                    risk_level = "🔴 CRITICAL"
                elif risk_score >= 500:
                    risk_level = "🟠 HIGH"
                elif risk_score >= 100:
                    risk_level = "🟡 MEDIUM"
                elif risk_score >= 10:
                    risk_level = "🟢 LOW"
                else:
                    risk_level = "⚪ MINIMAL"
                print(f"Risk Level: {risk_level}")
            
            print("-" * 60)
        
        # Enhanced threat summary
        print(f"\nTHREAT SUMMARY:")
        print("=" * 40)
        
        # Categorize by actual risk scores
        critical_count = len([m for m in matches if isinstance(m['data'].get('total_risk_score'), (int, float)) and m['data']['total_risk_score'] >= 1000])
        high_count = len([m for m in matches if isinstance(m['data'].get('total_risk_score'), (int, float)) and 500 <= m['data']['total_risk_score'] < 1000])
        medium_count = len([m for m in matches if isinstance(m['data'].get('total_risk_score'), (int, float)) and 100 <= m['data']['total_risk_score'] < 500])
        low_count = len([m for m in matches if isinstance(m['data'].get('total_risk_score'), (int, float)) and 10 <= m['data']['total_risk_score'] < 100])
        minimal_count = len([m for m in matches if isinstance(m['data'].get('total_risk_score'), (int, float)) and m['data']['total_risk_score'] < 10])
        
        if critical_count > 0:
            print(f"🔴 CRITICAL (≥1000):  {critical_count} extensions")
        if high_count > 0:
            print(f"🟠 HIGH (500-999):    {high_count} extensions")
        if medium_count > 0:
            print(f"🟡 MEDIUM (100-499):  {medium_count} extensions")
        if low_count > 0:
            print(f"🟢 LOW (10-99):       {low_count} extensions")
        if minimal_count > 0:
            print(f"⚪ MINIMAL (<10):     {minimal_count} extensions")
        
        # Show ranking distribution
        print(f"\nRANKING DISTRIBUTION:")
        print("=" * 40)
        total_extensions = len(extensions_data)
        top_1_percent = total_extensions * 0.01
        top_5_percent = total_extensions * 0.05
        top_10_percent = total_extensions * 0.10
        
        top_1_count = len([m for m in matches if isinstance(m['rank'], int) and m['rank'] <= top_1_percent])
        top_5_count = len([m for m in matches if isinstance(m['rank'], int) and m['rank'] <= top_5_percent]) - top_1_count
        top_10_count = len([m for m in matches if isinstance(m['rank'], int) and m['rank'] <= top_10_percent]) - top_1_count - top_5_count
        
        if top_1_count > 0:
            print(f"Top 1% Riskiest:   {top_1_count} extensions")
        if top_5_count > 0:
            print(f"Top 5% Riskiest:   {top_5_count} extensions")
        if top_10_count > 0:
            print(f"Top 10% Riskiest:  {top_10_count} extensions")
        
        # Show average risk score of suspicious extensions
        risk_scores = [m['data'].get('total_risk_score') for m in matches if isinstance(m['data'].get('total_risk_score'), (int, float))]
        if risk_scores:
            avg_suspicious_risk = sum(risk_scores) / len(risk_scores)
            overall_avg = data.get('analysis_summary', {}).get('average_risk_score', 0)
            print(f"\nRISK COMPARISON:")
            print("=" * 40)
            print(f"Average Risk (Suspicious): {avg_suspicious_risk:.2f}")
            print(f"Average Risk (Overall):    {overall_avg:.2f}")
            print(f"Risk Multiplier:           {avg_suspicious_risk/overall_avg:.1f}x higher" if overall_avg > 0 else "")
        
    else:
        print(f"\n✅ No suspicious extensions found in your risk analysis")
        print(f"   Checked {len(extensions_data)} extensions against {len(suspicious_ids)} suspicious IDs")

def main():
    """Main function to extract IDs and check risk analysis file."""
    print("EmPoWeb Suspicious Extension Risk Analysis Checker")
    print("=" * 60)
    
    # Extract suspicious extension IDs
    suspicious_ids = extract_suspicious_extension_ids()
    print(f"Extracted {len(suspicious_ids)} suspicious extension IDs from the EmPoWeb paper")
    
    # Save to file
    save_suspicious_ids(suspicious_ids)
    
    # Check risk analysis file
    print(f"\nChecking risk analysis file...")
    
    # Ask for file path
    file_path = input("Enter path to 'all_extensions_ranked.json' (or press Enter for current directory): ").strip()
    if not file_path:
        file_path = "all_extensions_ranked.json"
    
    check_risk_analysis_file(suspicious_ids, file_path)

if __name__ == "__main__":
    main()