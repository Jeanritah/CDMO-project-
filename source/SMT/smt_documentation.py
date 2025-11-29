# CDMO_Project/source/SMT/final_comparison.py
import json
import os

def generate_comprehensive_analysis():
    """Generating comprehensive analysis for  report"""
    
    # All the  experimental data
    data = {
        "n": [6, 8, 10, 12, 14],
        "smt_original": [0.000, 1.000, 140.000, 300, 300],
        "smt_optimized": [0.046, 4.589, 116.039, 300, "N/A"],
        "cp": [0.003, 0.004, 0.541, 9.546, 241.026]
    }
    
    print("=== COMPREHENSIVE PERFORMANCE ANALYSIS ===")
    
    print("\nTable 1: Detailed Performance Comparison")
    print("| n  | SMT Original | SMT Optimized |     CP     | Best Approach |")
    print("|----|--------------|---------------|------------|---------------|")
    
    for i in range(len(data["n"])):
        n = data["n"][i]
        smt_orig = data["smt_original"][i]
        smt_opt = data["smt_optimized"][i] 
        cp = data["cp"][i]
        
        # Determine best approach
        if smt_orig == 300 and smt_opt == 300:
            best = "CP only"
        elif isinstance(smt_orig, (int, float)) and isinstance(cp, (int, float)):
            if smt_orig < cp:
                best = "SMT Original"
            else:
                best = "CP"
        else:
            best = "CP"
            
        print(f"| {n:2} | {smt_orig:12.3f} | {smt_opt:13.3f} | {cp:10.3f} | {best:^13} |")
    
    print("\nTable 2: Performance Ratios (SMT/CP)")
    print("| n  | Original Ratio | Optimized Ratio | Improvement |")
    print("|----|----------------|-----------------|-------------|")
    
    for i in range(len(data["n"])):
        n = data["n"][i]
        smt_orig = data["smt_original"][i]
        smt_opt = data["smt_optimized"][i]
        cp = data["cp"][i]
        
        if smt_orig != 300 and cp != 300:
            orig_ratio = smt_orig / cp
            opt_ratio = smt_opt / cp if smt_opt != 300 else "Timeout"
            improvement = ((smt_orig - smt_opt) / smt_orig * 100) if smt_opt != 300 else "N/A"
            
            print(f"| {n:2} | {orig_ratio:14.1f}x | {str(opt_ratio):15} | {str(improvement):>11} |")
        else:
            print(f"| {n:2} | {'Timeout':>14} | {'Timeout':>15} | {'N/A':>11} |")
    
    print("\n" + "="*70)
    print("KEY FINDINGS FOR the REPORT")
    print("="*70)
    
    print("\n1. PERFORMANCE PATTERNS:")
    print("   - SMT works well for very small instances (n=6)")
    print("   - CP dominates for n ≥ 8")
    print("   - Optimizations helped for n=10 (18% improvement)")
    print("   - Both SMT versions timeout at n=12")
    
    print("\n2. SCALABILITY ANALYSIS:")
    print("   - CP scales linearly up to n=14")
    print("   - SMT performance degrades rapidly after n=8")
    print("   - The performance gap widens with problem size")
    
    print("\n3. OPTIMIZATION EFFECTIVENESS:")
    print("   ✅ n=10: 18% improvement with optimizations")
    print("   ❌ n=8: Optimizations made it slower")
    print("   ⚠️  n=12: Still times out despite optimizations")
    
    print("\n4. PRACTICAL RECOMMENDATIONS:")
    print("   - Use CP for n ≥ 8")
    print("   - SMT viable only for n ≤ 6")
    print("   - For large instances, CP is the only option")

def generate_technical_insights():
    """Generating  technical insights for the  report discussion"""
    
    print("\n" + "="*70)
    print("TECHNICAL INSIGHTS FOR DISCUSSION SECTION")
    print("="*70)
    
    print("\nWhy CP Performs Better:")
    print("1. GLOBAL CONSTRAINT PROPAGATION")
    print("   - CP's alldifferent and global_cardinality constraints")
    print("   - Efficient domain reduction and propagation")
    print("   - Specialized algorithms for combinatorial problems")
    
    print("\n2. SEARCH STRATEGIES") 
    print("   - CP solvers like Gecode have sophisticated search heuristics")
    print("   - Better variable and value selection strategies")
    print("   - Restart strategies with learning")
    
    print("\n3. PROBLEM STRUCTURE")
    print("   - STS has strong combinatorial structure")
    print("   - Benefits from CP's discrete reasoning")
    print("   - Less benefit from SMT's theory reasoning")
    
    print("\nSMT Strengths and Limitations:")
    print("✅ THEORY INTEGRATION")
    print("   - Can combine multiple theories (integers, arrays, etc.)")
    print("   - Good for problems with arithmetic constraints")
    print("   - Strong for optimization with objective functions")
    
    print("❌ COMBINATORIAL OVERHEAD")
    print("   - Theory reasoning adds overhead")
    print("   - Less efficient for pure satisfaction problems")
    print("   - Larger search space for combinatorial problems")

def generate_conclusion_recommendations():
    """Generate conclusion and recommendations"""
    
    print("\n" + "="*70)
    print("CONCLUSION AND RECOMMENDATIONS")
    print("="*70)
    
    print("\nSummary of Findings:")
    print("1. For the STS problem, CP is clearly superior to SMT")
    print("2. SMT is only competitive for very small instances (n ≤ 6)")
    print("3. The performance gap increases significantly with problem size")
    print("4. SMT optimizations provide limited benefits")
    
    print("\nRecommendations:")
    print("🔷 USE CP WHEN:")
    print("   - Problem size n ≥ 8")
    print("   - Dealing with combinatorial satisfaction problems") 
    print("   - Global constraints are natural fit")
    print("   - Performance is critical")
    
    print("🔷 CONSIDER SMT WHEN:")
    print("   - Very small problem instances")
    print("   - Problems require complex theory combinations")
    print("   - Optimization with complex objective functions")
    print("   - Integration with other SMT-solvable subproblems")
    
    print("\nFuture Work:")
    print("1. Explore hybrid CP-SAT approaches")
    print("2. Investigate SMT with different theories")
    print("3. Test optimization version with objective functions")
    print("4. Compare with MIP approaches")

def create_report_ready_tables():
    """Creating  formatted tables for the report"""
    
    print("\n" + "="*70)
    print("REPORT-READY TABLES (Copy these directly)")
    print("="*70)
    
    print("\n\\begin{table}[h]")
    print("\\centering")
    print("\\caption{Performance comparison: SMT vs CP}")
    print("\\label{tab:performance}")
    print("\\begin{tabular}{|c|r|r|r|r|}")
    print("\\hline")
    print("\\textbf{n} & \\textbf{SMT (s)} & \\textbf{SMT Opt (s)} & \\textbf{CP (s)} & \\textbf{Ratio} \\\\")
    print("\\hline")
    
    data = {
        "n": [6, 8, 10, 12, 14],
        "smt_orig": [0.000, 1.000, 140.000, 300, 300],
        "smt_opt": [0.046, 4.589, 116.039, 300, "---"],
        "cp": [0.003, 0.004, 0.541, 9.546, 241.026]
    }
    
    for i in range(len(data["n"])):
        n = data["n"][i]
        smt_o = data["smt_orig"][i]
        smt_opt = data["smt_opt"][i]
        cp = data["cp"][i]
        
        if smt_o != 300 and cp != 300:
            ratio = smt_o / cp
            ratio_str = f"{ratio:.1f}x"
        else:
            ratio_str = "Timeout"
            
        print(f"{n} & {smt_o:.3f} & {smt_opt} & {cp:.3f} & {ratio_str} \\\\")
    
    print("\\hline")
    print("\\end{tabular}")
    print("\\end{table}")

if __name__ == "__main__":
    generate_comprehensive_analysis()
    generate_technical_insights() 
    generate_conclusion_recommendations()
    create_report_ready_tables()
