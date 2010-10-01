/**
 * Parses all the files in a directory, writing the results to a new
 * directory.  The two command-line arguments are inputDir and
 * outputDir.  The output format is, for each line:
 *  
 * <sentence>
 * <str>the original string</str>
 * <penn>
 * the Penn Treebank parse
 * on multiple lines
 * </penn>
 * <dep>
 * Stanford dependencies parse on one line
 * </dep>
 * </sentence>
 * 
 * 
 * Compile: javac -cp stanford-parser.jar StanfordDirectoryParser.java
 * Run: java -mx2000m -cp "stanford-parser.jar:$CLASSPATH" StanfordDirectoryParser inputdir outputdir
 * 
 * @author Chris Potts, 2010-10-01
 * 
 */

import java.util.*;
import edu.stanford.nlp.trees.*;
import edu.stanford.nlp.process.DocumentPreprocessor;
import edu.stanford.nlp.objectbank.TokenizerFactory;
import edu.stanford.nlp.process.PTBTokenizer;
import edu.stanford.nlp.parser.lexparser.LexicalizedParser;

import java.io.*;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

class StanfordDirectoryParser {
    public static void main(String[] args) throws IOException {
	
	LexicalizedParser lp = new LexicalizedParser("englishPCFG.ser.gz");
	lp.setOptionFlags(new String[]{"-retainTmpSubcategories"});
	TreebankLanguagePack tlp = new PennTreebankLanguagePack();
	GrammaticalStructureFactory gsf = tlp.grammaticalStructureFactory();
	
	final String INPUT_DIR = args[0];
	final String OUTPUT_DIR = args[1];
        
	File[] filenames = new File(INPUT_DIR).listFiles();
	
	for (int i = 0; i < filenames.length; i++) {

	    if (filenames[i].getName().endsWith(".txt")) {
		    
		String outputStr = "";
		
		BufferedReader input = new BufferedReader(new InputStreamReader(new FileInputStream(filenames[i]), "UTF8"));

		String line = null; 
		while ((line = input.readLine()) != null) {
		    // Treebank parse.
		    Tree parse = (Tree) lp.apply(line);
		    // Dependency structure
		    GrammaticalStructure gs = gsf.newGrammaticalStructure(parse);
		    Collection tdl = gs.typedDependenciesCollapsed();
		    // Output.
		    String parsedString = "<sentence>\n<str>" + line + "</str>\n<penn>\n" + parse.pennString() + "</penn>\n<dep>\n" + tdl + "\n</dep>\n</sentence>\n";
		    outputStr += parsedString;
		}
		// Create file
		Writer output = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(OUTPUT_DIR + "/" + filenames[i].getName()), "UTF8"));
		try {
		    output.write( outputStr );
		}
		finally {
		    output.close();
		}
		System.out.println(i + " " + filenames[i]); 
	    }				
	}
    }
}
