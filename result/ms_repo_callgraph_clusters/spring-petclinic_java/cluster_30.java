// Cluster 30

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
package org.springframework.samples.petclinic.system;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

/**
 * Controller used to showcase what happens when an exception is thrown
 *
 * @author Michael Isvy
 * <p/>
 * Also see how a view that resolves to "error" has been added ("error.html").
 */
@Controller
class CrashController {

	@GetMapping("/oups")
	public String triggerException() {
		throw new RuntimeException(
				"Expected: controller used to showcase what " + "happens when an exception is thrown");
	}

}


// Node: triggerException
// Node: RuntimeException
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

package org.springframework.samples.petclinic.system;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThatExceptionOfType;

/**
 * Test class for {@link CrashController}
 *
 * @author Colin But
 * @author Alex Lutz
 */
// Waiting https://github.com/spring-projects/spring-boot/issues/5574 ..good
// luck ((plain(st) UNIT test)! :)
class CrashControllerTests {

	final CrashController testee = new CrashController();

	@Test
	void testTriggerException() {
		assertThatExceptionOfType(RuntimeException.class).isThrownBy(() -> testee.triggerException())
			.withMessageContaining("Expected: controller used to showcase what happens when an exception is thrown");
	}

}


// Node: testTriggerException
// Node: assertThatExceptionOfType
// Node: isThrownBy
// Node: withMessageContaining
