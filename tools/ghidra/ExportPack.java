// Headless export for tools/ghidra/export_pack.py. Writes machine-readable facts about functions
// of an already analyzed program; the Python driver decides suitability and assembles packs.
// Everything this script writes is derived from the program under analysis and must stay in a
// private directory.
//
// Script args: <rva list file | @random:N:SEED> <output dir> <mode: full | refs>
//   meta.tsv   rva found name entry_count body_ranges n_instr computed_jumps computed_targets thunk
//              fp_arith cond_branches indirect_calls
//   refs.tsv   rva from_offset ref_type target_rva mnemonic operand_index target_names target_func_entry
//   full mode also writes <output dir>/<rva hex>/listing.txt and decompiled.c
// @category SkyrimResearch

import java.io.*;
import java.nio.file.*;
import java.util.*;

import ghidra.app.decompiler.*;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.symbol.*;

public class ExportPack extends GhidraScript {
    private long base;
    // Scalar and packed SSE arithmetic: enough to tell floating-point code from integer code.
    private static final java.util.regex.Pattern FP_ARITH =
        java.util.regex.Pattern.compile("(?i)(ADD|SUB|MUL|DIV|SQRT|MIN|MAX)(SS|SD|PS|PD)");

    private static String clean(String s) {
        return s.replace('\t', ' ').replace('\n', ' ').replace('\r', ' ');
    }

    private String names(Address a) {
        List<String> out = new ArrayList<>();
        for (Symbol s : currentProgram.getSymbolTable().getSymbols(a)) out.add(clean(s.getName(true)));
        return out.isEmpty() ? "-" : String.join(" | ", out);
    }

    private List<Long> selectRvas(String spec, FunctionManager fm) throws IOException {
        List<Long> rvas = new ArrayList<>();
        if (spec.startsWith("@random:")) {
            String[] p = spec.split(":");
            int n = Integer.parseInt(p[1]);
            List<Long> all = new ArrayList<>();
            MemoryBlock text = currentProgram.getMemory().getBlock(".text");
            for (Function f : fm.getFunctions(true)) {
                // Only functions in the main code section: other blocks hold thunks and middleware
                // stubs whose shape says little about engine code.
                if (text != null && text.contains(f.getEntryPoint())) all.add(f.getEntryPoint().getOffset() - base);
            }
            Collections.shuffle(all, new Random(Long.parseLong(p[2])));
            rvas.addAll(all.subList(0, Math.min(n, all.size())));
            Collections.sort(rvas);
            return rvas;
        }
        for (String line : Files.readAllLines(Paths.get(spec))) {
            line = line.trim();
            if (line.isEmpty() || line.startsWith("#")) continue;
            rvas.add(Long.decode(line.split("\\s+")[0]));
        }
        return rvas;
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        base = currentProgram.getImageBase().getOffset();
        FunctionManager fm = currentProgram.getFunctionManager();
        List<Long> rvas = selectRvas(args[0], fm);
        File outDir = new File(args[1]);
        boolean full = args[2].equals("full");
        outDir.mkdirs();
        PrintWriter meta = new PrintWriter(new FileWriter(new File(outDir, "meta.tsv")));
        PrintWriter refs = new PrintWriter(new FileWriter(new File(outDir, "refs.tsv")));
        DecompInterface di = null;
        if (full) {
            di = new DecompInterface();
            di.openProgram(currentProgram);
        }
        Listing listing = currentProgram.getListing();
        for (long rva : rvas) {
            if (monitor.isCancelled()) break;
            Address entry = toAddr(base + rva);
            Function f = fm.getFunctionAt(entry);
            if (f == null) {
                meta.printf("0x%x\t0\t%s\t0\t-\t0\t0\t0\t0\t0\t0\t0%n", rva, names(entry));
                continue;
            }
            AddressSetView body = f.getBody();
            StringBuilder ranges = new StringBuilder();
            for (AddressRange r : body) {
                if (ranges.length() > 0) ranges.append(',');
                ranges.append(String.format("0x%x-0x%x", r.getMinAddress().getOffset() - base,
                                            r.getMaxAddress().getOffset() - base + 1));
            }
            int nInstr = 0, computed = 0, fpArith = 0, condBranches = 0, indirectCalls = 0;
            Set<Address> computedTargets = new HashSet<>();
            StringBuilder text = new StringBuilder();
            for (Instruction ins : listing.getInstructions(body, true)) {
                nInstr++;
                long off = ins.getAddress().getOffset() - entry.getOffset();
                boolean isComputed = ins.getFlowType().isComputed() && ins.getFlowType().isJump();
                if (isComputed) computed++;
                if (FP_ARITH.matcher(ins.getMnemonicString()).matches()) fpArith++;
                if (ins.getFlowType().isConditional() && ins.getFlowType().isJump()) condBranches++;
                if (ins.getFlowType().isComputed() && ins.getFlowType().isCall()) indirectCalls++;
                StringBuilder refText = new StringBuilder();
                for (Reference r : ins.getReferencesFrom()) {
                    Address t = r.getToAddress();
                    if (!t.isMemoryAddress()) continue;
                    if (isComputed && r.getReferenceType().isFlow()) computedTargets.add(t);
                    long trva = t.getOffset() - base;
                    Function tf = fm.getFunctionContaining(t);
                    long tentry = tf == null ? -1 : tf.getEntryPoint().getOffset() - base;
                    String tnames = names(t);
                    refs.printf("0x%x\t%d\t%s\t0x%x\t%s\t%d\t%s\t%d%n", rva, off, r.getReferenceType(), trva,
                                clean(ins.getMnemonicString()), r.getOperandIndex(), tnames, tentry);
                    refText.append(String.format(" [%s 0x%x %s]", r.getReferenceType(), trva, tnames));
                }
                if (full) text.append(String.format("  +0x%03x  %-48s%s%n", off, ins.toString(), refText));
            }
            meta.printf("0x%x\t1\t%s\t%d\t%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d%n", rva, clean(f.getName(true)),
                        currentProgram.getSymbolTable().getSymbols(entry).length, ranges, nInstr, computed,
                        computedTargets.size(), f.isThunk() ? 1 : 0, fpArith, condBranches, indirectCalls);
            if (full) {
                File dir = new File(outDir, String.format("%x", rva));
                dir.mkdirs();
                try (PrintWriter w = new PrintWriter(new FileWriter(new File(dir, "listing.txt")))) {
                    w.printf("function %s at rva 0x%x%nsignature (Ghidra) %s%nbody %s%n%n", f.getName(true), rva,
                             f.getSignature(), ranges);
                    w.print(text);
                }
                DecompileResults res = di.decompileFunction(f, 60, monitor);
                try (PrintWriter w = new PrintWriter(new FileWriter(new File(dir, "decompiled.c")))) {
                    w.println(res.decompileCompleted() ? res.getDecompiledFunction().getC()
                                                       : "// decompiler failed: " + res.getErrorMessage());
                }
            }
        }
        if (di != null) di.dispose();
        meta.close();
        refs.close();
    }
}
