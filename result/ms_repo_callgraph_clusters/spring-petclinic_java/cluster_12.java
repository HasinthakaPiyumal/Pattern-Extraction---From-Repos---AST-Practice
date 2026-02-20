// Cluster 12

/*
 * Copyright 2012-2025 the original author or authors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.springframework.samples.petclinic.owner;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

import org.springframework.core.style.ToStringCreator;
import org.springframework.samples.petclinic.model.Person;
import org.springframework.util.Assert;

import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.OneToMany;
import jakarta.persistence.OrderBy;
import jakarta.persistence.Table;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.NotBlank;

/**
 * Simple JavaBean domain object representing an owner.
 *
 * @author Ken Krebs
 * @author Juergen Hoeller
 * @author Sam Brannen
 * @author Michael Isvy
 * @author Oliver Drotbohm
 * @author Wick Dynex
 */
@Entity
@Table(name = "owners")
public class Owner extends Person {

	@Column
	@NotBlank
	private String address;

	@Column
	@NotBlank
	private String city;

	@Column
	@NotBlank
	@Pattern(regexp = "\\d{10}", message = "{telephone.invalid}")
	private String telephone;

	@OneToMany(cascade = CascadeType.ALL, fetch = FetchType.EAGER)
	@JoinColumn(name = "owner_id")
	@OrderBy("name")
	private final List<Pet> pets = new ArrayList<>();

	public String getAddress() {
		return this.address;
	}

	public void setAddress(String address) {
		this.address = address;
	}

	public String getCity() {
		return this.city;
	}

	public void setCity(String city) {
		this.city = city;
	}

	public String getTelephone() {
		return this.telephone;
	}

	public void setTelephone(String telephone) {
		this.telephone = telephone;
	}

	public List<Pet> getPets() {
		return this.pets;
	}

	public void addPet(Pet pet) {
		if (pet.isNew()) {
			getPets().add(pet);
		}
	}

	/**
	 * Return the Pet with the given name, or null if none found for this Owner.
	 * @param name to test
	 * @return the Pet with the given name, or null if no such Pet exists for this Owner
	 */
	public Pet getPet(String name) {
		return getPet(name, false);
	}

	/**
	 * Return the Pet with the given id, or null if none found for this Owner.
	 * @param id to test
	 * @return the Pet with the given id, or null if no such Pet exists for this Owner
	 */
	public Pet getPet(Integer id) {
		for (Pet pet : getPets()) {
			if (!pet.isNew()) {
				Integer compId = pet.getId();
				if (Objects.equals(compId, id)) {
					return pet;
				}
			}
		}
		return null;
	}

	/**
	 * Return the Pet with the given name, or null if none found for this Owner.
	 * @param name to test
	 * @param ignoreNew whether to ignore new pets (pets that are not saved yet)
	 * @return the Pet with the given name, or null if no such Pet exists for this Owner
	 */
	public Pet getPet(String name, boolean ignoreNew) {
		for (Pet pet : getPets()) {
			String compName = pet.getName();
			if (compName != null && compName.equalsIgnoreCase(name)) {
				if (!ignoreNew || !pet.isNew()) {
					return pet;
				}
			}
		}
		return null;
	}

	@Override
	public String toString() {
		return new ToStringCreator(this).append("id", this.getId())
			.append("new", this.isNew())
			.append("lastName", this.getLastName())
			.append("firstName", this.getFirstName())
			.append("address", this.address)
			.append("city", this.city)
			.append("telephone", this.telephone)
			.toString();
	}

	/**
	 * Adds the given {@link Visit} to the {@link Pet} with the given identifier.
	 * @param petId the identifier of the {@link Pet}, must not be {@literal null}.
	 * @param visit the visit to add, must not be {@literal null}.
	 */
	public void addVisit(Integer petId, Visit visit) {

		Assert.notNull(petId, "Pet identifier must not be null!");
		Assert.notNull(visit, "Visit must not be null!");

		Pet pet = getPet(petId);

		Assert.notNull(pet, "Invalid Pet identifier!");

		pet.addVisit(visit);
	}

}


// Node: toString
// Node: ToStringCreator
// Node: append
/*
 * Copyright 2012-2025 the original author or authors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.springframework.samples.petclinic.model;

import jakarta.persistence.Column;
import jakarta.persistence.MappedSuperclass;
import jakarta.validation.constraints.NotBlank;

/**
 * Simple JavaBean domain object adds a name property to <code>BaseEntity</code>. Used as
 * a base class for objects needing these properties.
 *
 * @author Ken Krebs
 * @author Juergen Hoeller
 * @author Wick Dynex
 */
@MappedSuperclass
public class NamedEntity extends BaseEntity {

	@Column
	@NotBlank
	private String name;

	public String getName() {
		return this.name;
	}

	public void setName(String name) {
		this.name = name;
	}

	@Override
	public String toString() {
		String name = this.getName();
		return (name != null) ? name : "<null>";
	}

}


package org.springframework.samples.petclinic.system;

import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.nio.file.*;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Properties;
import java.util.Set;
import java.util.TreeSet;
import java.util.regex.Pattern;
import java.util.stream.Stream;

import static org.junit.jupiter.api.Assertions.fail;

/**
 * This test ensures that there are no hard-coded strings without internationalization in
 * any HTML files. Also ensures that a string is translated in every language to avoid
 * partial translations.
 *
 * @author Anuj Ashok Potdar
 */
public class I18nPropertiesSyncTest {

	private static final String I18N_DIR = "src/main/resources";

	private static final String BASE_NAME = "messages";

	public static final String PROPERTIES = ".properties";

	private static final Pattern HTML_TEXT_LITERAL = Pattern.compile(">([^<>{}]+)<");

	private static final Pattern BRACKET_ONLY = Pattern.compile("<[^>]*>\\s*[\\[\\]](?:&nbsp;)?\\s*</[^>]*>");

	private static final Pattern HAS_TH_TEXT_ATTRIBUTE = Pattern.compile("th:(u)?text\\s*=\\s*\"[^\"]+\"");

	@Test
	public void checkNonInternationalizedStrings() throws IOException {
		Path root = Paths.get("src/main");
		List<Path> files;

		try (Stream<Path> stream = Files.walk(root)) {
			files = stream.filter(p -> p.toString().endsWith(".java") || p.toString().endsWith(".html"))
				.filter(p -> !p.toString().contains("/test/"))
				.filter(p -> !p.getFileName().toString().endsWith("Test.java"))
				.toList();
		}

		StringBuilder report = new StringBuilder();

		for (Path file : files) {
			List<String> lines = Files.readAllLines(file);
			for (int i = 0; i < lines.size(); i++) {
				String line = lines.get(i).trim();

				if (line.startsWith("//") || line.startsWith("@") || line.contains("log.")
						|| line.contains("System.out"))
					continue;

				if (file.toString().endsWith(".html")) {
					boolean hasLiteralText = HTML_TEXT_LITERAL.matcher(line).find();
					boolean hasThTextAttribute = HAS_TH_TEXT_ATTRIBUTE.matcher(line).find();
					boolean isBracketOnly = BRACKET_ONLY.matcher(line).find();

					if (hasLiteralText && !line.contains("#{") && !hasThTextAttribute && !isBracketOnly) {
						report.append("HTML: ")
							.append(file)
							.append(" Line ")
							.append(i + 1)
							.append(": ")
							.append(line)
							.append("\n");
					}
				}
			}
		}

		if (!report.isEmpty()) {
			fail("Hardcoded (non-internationalized) strings found:\n" + report);
		}
	}

	@Test
	public void checkI18nPropertyFilesAreInSync() throws IOException {
		List<Path> propertyFiles;
		try (Stream<Path> stream = Files.walk(Paths.get(I18N_DIR))) {
			propertyFiles = stream.filter(p -> p.getFileName().toString().startsWith(BASE_NAME))
				.filter(p -> p.getFileName().toString().endsWith(PROPERTIES))
				.toList();
		}

		Map<String, Properties> localeToProps = new HashMap<>();

		for (Path path : propertyFiles) {
			Properties props = new Properties();
			try (var reader = Files.newBufferedReader(path)) {
				props.load(reader);
				localeToProps.put(path.getFileName().toString(), props);
			}
		}

		String baseFile = BASE_NAME + PROPERTIES;
		Properties baseProps = localeToProps.get(baseFile);
		if (baseProps == null) {
			fail("Base properties file '" + baseFile + "' not found.");
			return;
		}

		Set<String> baseKeys = baseProps.stringPropertyNames();
		StringBuilder report = new StringBuilder();

		for (Map.Entry<String, Properties> entry : localeToProps.entrySet()) {
			String fileName = entry.getKey();
			// We use fallback logic to include english strings, hence messages_en is not
			// populated.
			if (fileName.equals(baseFile) || fileName.equals("messages_en.properties"))
				continue;

			Properties props = entry.getValue();
			Set<String> missingKeys = new TreeSet<>(baseKeys);
			missingKeys.removeAll(props.stringPropertyNames());

			if (!missingKeys.isEmpty()) {
				report.append("Missing keys in ").append(fileName).append(":\n");
				missingKeys.forEach(k -> report.append("  ").append(k).append("\n"));
			}
		}

		if (!report.isEmpty()) {
			fail("Translation files are not in sync:\n" + report);
		}
	}

}


// Node: repos/cloned_ms_repos/spring-petclinic/src/test/java/org/springframework/samples/petclinic/system/I18nPropertiesSyncTest.java:I18nPropertiesSyncTest.<init>
// Node: compile
// Node: checkNonInternationalizedStrings
// Node: try
// Node: walk
// Node: filter
// Node: endsWith
// Node: contains
// Node: getFileName
// Node: StringBuilder
// Node: readAllLines
// Node: trim
// Node: matcher
// Node: find
// Node: fail
// Node: Hardcoded
// Node: checkI18nPropertyFilesAreInSync
// Node: Properties
// Node: newBufferedReader
// Node: load
// Node: stringPropertyNames
// Node: entrySet
// Node: getKey
// Node: getValue
// Node: removeAll
// Node: forEach
