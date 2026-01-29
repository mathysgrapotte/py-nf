# Call graph (what calls what)

This page documents the concrete call chains.

## Running an arbitrary Nextflow script

```text
pynf.run_script(...) or pynf.api.run_script(request)
  -> pynf.api.run_script
     -> pynf._core.execution.execute_nextflow(request, nextflow_jar_path?)
        -> (JAR resolve + JVM start)
        -> (Session init/start)
        -> loader.parse(script)
        -> get_process_inputs(...) (for validation)
        -> (optional) validate_inputs + to_java coercion
        -> register TraceObserverV2 proxy
        -> loader.runScript(); session.fireDataflowNetwork(False); session.await_()
        -> snapshot NextflowResult
```

## Running an nf-core module

```text
pynf.api.run_module(module_id, request, cache_dir, github_token)
  -> pynf._core.nfcore_modules.run_nfcore_module
     -> ensure_module(cache_dir, module_id)
        -> download main.nf + meta.yml if missing
     -> build module_request with script_path = cached main.nf
     -> pynf._core.execution.execute_nextflow(module_request)
```

## Introspecting module inputs

```text
pynf.api.get_module_inputs(module_id, cache_dir, github_token)
  -> pynf._core.nfcore_modules.get_module_inputs
     -> ensure_module(...)
     -> start_jvm_if_needed
     -> Session.init/start with cached main.nf
     -> loader.parse(main.nf)
     -> ScriptMeta.get(script) + walk process configs
     -> return channel definitions
```

## Where data is captured

- **Workflow output values**: `TraceObserverV2.onWorkflowOutput`
- **Published files**: `TraceObserverV2.onFilePublish`
- **Task work directories**: captured from task completion/cached events

All of these are snapshotted into `NextflowResult`.
