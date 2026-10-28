# Native dependency notices

The project worker/adapter sources use the repository's Apache-2.0 license.
No CUBRID source, native shared library or host system library is bundled in the
Python wheel. Native inputs are separately installed, hash-bound host artifacts.
The source distribution retains these notices alongside native worker sources.
[notices.json](../qualification/notices.json) records each retained text's original
path/hash, host package identities and the available native link recipe.

| Component and use | Retained terms |
| --- | --- |
| CUBRID parser, private headers, libcubridcs, messages and timezone runtime | [CUBRID-COPYING.txt](CUBRID-COPYING.txt), Apache-2.0 engine/BSD connector split; [CUBRID-CREDITS.txt](CUBRID-CREDITS.txt) preserves upstream component acknowledgments |
| CCI libcubridcs dynamic dependency, libcascci.so.11.2 | [CCI-COPYING.txt](CCI-COPYING.txt), including BSD-3-Clause connector terms |
| RapidJSON 1.1 headers compiled into the worker and included by CUBRID headers | [RapidJSON.txt](RapidJSON.txt), MIT plus upstream third-party notices; only headers are used, no bin/jsonchecker code |
| Expat static member of the supplied libcubridcs | [libexpat.txt](libexpat.txt), MIT-style terms |
| libedit static member of the supplied libcubridcs | [libedit.txt](libedit.txt), BSD terms |
| LZ4 static member of the supplied libcubridcs | [lz4.txt](lz4.txt), BSD-2-Clause library terms |
| RE2 static member of the supplied libcubridcs; type declarations in headers | [re2.txt](re2.txt), BSD-3-Clause terms |
| OpenSSL libssl/libcrypto static members in supplied libcubridcs | [libopenssl.txt](libopenssl.txt), upstream OpenSSL terms from the pinned CUBRID source |
| System OpenSSL 3 libcrypto used for worker SHA-256 | [OpenSSL-system.txt](OpenSSL-system.txt), Apache-2.0 and component notices for the installed library |
| GCC libstdc++ and libgcc runtime dependencies | [GCC-GPL3.txt](GCC-GPL3.txt), [GCC-LGPL3.txt](GCC-LGPL3.txt), [GCC-runtime-exception.txt](GCC-runtime-exception.txt) |
| glibc libc, libm and dynamic loader | [glibc-COPYING-LIB.txt](glibc-COPYING-LIB.txt), [glibc-COPYING.txt](glibc-COPYING.txt), [glibc-LICENSES.txt](glibc-LICENSES.txt), LGPL and bundled component notices |
| System zlib, a libcrypto dependency | [zlib.txt](zlib.txt), upstream README including zlib license |

The compiler-input record identifies the actual RapidJSON/CUBRID/OpenSSL headers.
Runtime file hashes and ldd results identify the supplied dynamic objects. The
available CUBRID link recipe whole-archives Expat, libedit, LZ4, OpenSSL and RE2;
these static components are included in the inventory even when their routines
are not reached by admitted parser inputs. CUBRID's own credits retain additional
source acknowledgments. No TBB, ODBC, JVM or full CUBRID installation is copied
into this project. This inventory does not claim reproducible provenance for
every byte of a separately built engine, or qualify a portable binary bundle.

Keep original copyright, license, disclaimer and attribution text with any native
artifact delivery. A future redistributed runtime must preserve its own complete
source/component notices and satisfy its actual dependencies' terms; this task
qualifies the exact existing host runtime and does not publish a binary bundle.
